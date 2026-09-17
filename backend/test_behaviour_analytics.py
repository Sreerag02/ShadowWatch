"""Executable behaviour report for any/all organization CSVs."""
import argparse
from pathlib import Path
import pandas as pd
from services.behaviour_analytics import analyze_behaviour

DATA_DIR=Path(__file__).resolve().parents[1]/'data'

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',choices=sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir()))
    parser.add_argument('--rule',choices=['R006','R007','R008','R009'])
    parser.add_argument('--summary',action='store_true')
    args=parser.parse_args(argv)
    folders=[DATA_DIR/args.dataset] if args.dataset else sorted(p for p in DATA_DIR.iterdir() if p.is_dir())
    print('SHADOWWATCH BEHAVIOUR ANALYTICS')
    for folder in folders:
        frames=[pd.read_csv(folder/f'{name}.csv') for name in ('investigations','cases','alerts')]
        print('\n'+folder.name)
        for rule,findings in analyze_behaviour(*frames).items():
            if args.rule and args.rule!=rule:continue
            print(rule,'findings:',len(findings))
            if not args.summary:
                for finding in findings.to_dict('records'):
                    print('Case:',finding.get('case_id',finding.get('case_ids')),'Reason:',finding['reason'])
    print('\nANALYSIS COMPLETE')

if __name__=='__main__':main()
