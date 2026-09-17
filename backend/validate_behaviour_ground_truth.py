"""Behaviour evaluation only; labels are loaded AFTER operational detection."""
import argparse
import json
from pathlib import Path
import pandas as pd
from services.behaviour_analytics import analyze_behaviour

DATA_DIR=Path(__file__).resolve().parents[1]/'data'
LABELS={'R006':{'REPETITIVE_INVESTIGATION'},'R007':{'INVESTIGATION_DURATION_ANOMALY'},
        'R008':{'REPEAT_INCIDENT','REPEAT_INCIDENT_PATTERN'},
        'R009':{'COMBINED_SUSPICIOUS_INVESTIGATION_BEHAVIOUR'}}

def metrics(expected,predicted):
    tp,fp,fn=len(expected&predicted),len(predicted-expected),len(expected-predicted)
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    return dict(TP=tp,FP=fp,FN=fn,precision=precision,recall=recall,
                f1=2*precision*recall/(precision+recall) if precision+recall else 0.0,
                false_positives=sorted(predicted-expected),false_negatives=sorted(expected-predicted))

def evaluate_rule(rule,findings,truth,cases,alerts):
    rows=truth[truth['problem_type'].isin(LABELS[rule])]
    positive=rows[rows['expected_detection'].astype(str).str.lower()=='true']
    if positive.empty:
        return dict(status='NOT_LABELLED',findings=len(findings),reason='No positive labels for this rule; precision/recall/F1 unavailable.')
    case_asset={r.case_id:r.asset_id for r in cases[['case_id','alert_id']].merge(alerts[['alert_id','asset_id']],on='alert_id').itertuples()}
    expected=set()
    for row in positive.to_dict('records'):
        if pd.notna(row.get('case_id')):
            expected.add(('case',str(row['case_id'])))
        elif pd.notna(row.get('asset_id')):
            expected.add(('asset',str(row['asset_id'])))
    units={key[0] for key in expected}
    predicted=set()
    for row in findings.to_dict('records'):
        ids=[row['case_id']] if row.get('case_id') else row['case_ids'].split(', ')
        if 'case' in units:
            predicted.update(('case',case) for case in ids)
        if 'asset' in units:
            assets={row['asset_id']} if row.get('asset_id') else {case_asset.get(case) for case in ids}
            predicted.update(('asset',asset) for asset in assets if asset)
    if not expected:
        return dict(status='UNMATCHABLE_LABELS',findings=len(findings))
    return dict(status='EVALUATED',units=sorted(units),findings=len(findings),**metrics(expected,predicted))

def evaluate_folder(folder):
    investigations=pd.read_csv(folder/'investigations.csv')
    cases=pd.read_csv(folder/'cases.csv')
    alerts=pd.read_csv(folder/'alerts.csv')
    findings=analyze_behaviour(investigations,cases,alerts)
    truth=pd.read_csv(folder/'ground_truth.csv')
    return {rule:evaluate_rule(rule,frame,truth,cases,alerts) for rule,frame in findings.items()}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',choices=sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir()))
    parser.add_argument('--rule',choices=sorted(LABELS))
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args(argv)
    folders=[DATA_DIR/args.dataset] if args.dataset else sorted(p for p in DATA_DIR.iterdir() if p.is_dir())
    report={p.name:{r:v for r,v in evaluate_folder(p).items() if not args.rule or r==args.rule} for p in folders}
    evaluated=[v for rules in report.values() for v in rules.values() if v['status']=='EVALUATED']
    tp,fp,fn=(sum(r[k] for r in evaluated) for k in ('TP','FP','FN'))
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    overall=dict(TP=tp,FP=fp,FN=fn,precision=precision,recall=recall,
                 f1=2*precision*recall/(precision+recall) if precision+recall else 0.0,
                 scope='Micro-average of labelled entity/rule units only; unlabelled rules excluded.') if evaluated else None
    if args.json:
        print(json.dumps(dict(organizations=report,overall=overall),indent=2))
    else:
        print('SHADOWWATCH BEHAVIOUR VALIDATION\nUnlabelled detections count as FP only in evaluated entity/rule strata; labels may be incomplete.')
        for organization,rules in report.items():
            print('\n'+organization)
            for rule,result in rules.items():
                print(rule,json.dumps(result))
        print('\nOVERALL',json.dumps(overall))
        print('R004 FAST_CRITICAL_CLOSURE and KPI_GAMING_PATTERN are not R007/R009 labels.')

if __name__=='__main__':main()
