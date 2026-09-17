import unittest
from datetime import datetime,timedelta
import pandas as pd
from services.behaviour_analytics import (
 detect_repetitive_investigations,detect_duration_anomalies,detect_repeat_incidents,
 detect_combined_suspicious_behaviour,analyze_behaviour)
from validate_behaviour_ground_truth import evaluate_rule

NOTE='Reviewed authentication logs and endpoint process records with supporting evidence.'
def dataset(durations=(60,60,60,60,60,60,2,900)):
    start=datetime(2026,1,1)
    inv=[];cases=[];alerts=[]
    for i,duration in enumerate(durations):
        inv.append(dict(investigation_id=f'I{i}',case_id=f'C{i}',analyst_id=None,analyst_notes=NOTE,
                        started_at=start,completed_at=start+timedelta(minutes=duration)))
        cases.append(dict(case_id=f'C{i}',alert_id=f'A{i}',entity_id='E1',closure_reason='ordinary closure'))
        alerts.append(dict(alert_id=f'A{i}',entity_id='E1',asset_id='AS1',timestamp=start+timedelta(days=i),
                           severity='HIGH',category='MALWARE'))
    return pd.DataFrame(inv),pd.DataFrame(cases),pd.DataFrame(alerts)

class BehaviourTests(unittest.TestCase):
    def test_identical_without_internal_repetition(self):
        inv,cases,_=dataset((60,60,60))
        result=detect_repetitive_investigations(inv,cases_df=cases)
        self.assertEqual(len(result),3)
        self.assertTrue(all(result['similarity_score']>.99))
        self.assertEqual(set(result['entity_id']),{'E1'})

    def test_empty_generic_and_stopword_notes(self):
        for value in (None,'','ok','the and or but if then for with'):
            inv,cases,_=dataset((60,60,60));inv['analyst_notes']=value
            self.assertTrue(detect_repetitive_investigations(inv,cases_df=cases).empty)

    def test_distinct_notes(self):
        inv,cases,_=dataset((60,60,60))
        inv['analyst_notes']=['Malware executable isolated quarantined disk sandbox payload analysis',
                             'Firewall network router blocked subnet traffic switch connection',
                             'Mailbox phishing sender email attachment recipient domain delivery']
        self.assertTrue(detect_repetitive_investigations(inv,cases_df=cases).empty)

    def test_entity_and_case_isolation(self):
        inv,cases,_=dataset((60,60,60));cases.loc[2,'entity_id']='E2'
        self.assertTrue(detect_repetitive_investigations(inv,cases_df=cases).empty)
        inv,cases,_=dataset((60,60,60));inv['case_id']='C0'
        self.assertTrue(detect_repetitive_investigations(inv,cases_df=cases).empty)

    def test_note_shuffle_and_duplicates_deterministic(self):
        inv,cases,_=dataset((60,60,60))
        first=detect_repetitive_investigations(inv,cases_df=cases)
        second=detect_repetitive_investigations(pd.concat([inv.iloc[::-1],inv.iloc[:1]]),cases_df=cases)
        self.assertEqual(first.to_dict('records'),second.to_dict('records'))

    def test_short_long_noncritical_no_closure_phrase(self):
        inv,cases,alerts=dataset()
        result=detect_duration_anomalies(inv,cases,alerts)
        self.assertEqual(set(result['direction']),{'SHORT','LONG'})
        self.assertEqual(set(result['case_id']),{'C6','C7'})
        self.assertTrue(all(result['baseline_duration_minutes']==60))
        self.assertEqual(set(result['severity']),{'HIGH'})

    def test_invalid_sparse_and_zero_baselines(self):
        inv,cases,alerts=dataset((0,0,0,0,0,0,60))
        self.assertTrue(detect_duration_anomalies(inv,cases,alerts).empty)
        inv,cases,alerts=dataset((60,2))
        self.assertTrue(detect_duration_anomalies(inv,cases,alerts).empty)
        inv,cases,alerts=dataset();inv['started_at']=None
        self.assertTrue(detect_duration_anomalies(inv,cases,alerts).empty)
        inv,cases,alerts=dataset();inv['completed_at']=datetime(2025,1,1)
        self.assertTrue(detect_duration_anomalies(inv,cases,alerts).empty)

    def test_duration_baselines_not_cross_entity_category_or_severity(self):
        inv,cases,alerts=dataset()
        for key in ('entity_id','category','severity'):
            changed=alerts.copy(); changed.loc[6:,key]='OTHER'
            c=cases.copy()
            if key=='entity_id':c.loc[6:,key]='OTHER'
            self.assertTrue(detect_duration_anomalies(inv,c,changed).empty)

    def test_r008_all_records_and_later_episode(self):
        _,cases,alerts=dataset([60]*10)
        alerts.loc[6:,'timestamp']+=timedelta(days=30)
        result=detect_repeat_incidents(alerts,cases)
        self.assertEqual(list(result['incident_count']),[6,4])
        self.assertIn('C5',result.iloc[0]['case_ids'])
        self.assertIn('C9',result.iloc[1]['case_ids'])
        self.assertEqual(result.to_dict('records'),detect_repeat_incidents(alerts.iloc[::-1],cases.iloc[::-1]).to_dict('records'))

    def test_r008_counts_alerts_not_multiple_cases(self):
        _,cases,alerts=dataset((60,))
        cases=pd.concat([cases.assign(case_id=f'C{i}') for i in range(6)])
        self.assertTrue(detect_repeat_incidents(alerts,cases).empty)

    def test_r008_boundaries_and_cross_entity_links(self):
        _,cases,alerts=dataset([60]*4)
        alerts.loc[3,'timestamp']=datetime(2026,1,11)
        self.assertEqual(len(detect_repeat_incidents(alerts,cases)),1)
        alerts.loc[3,'timestamp']+=timedelta(seconds=1)
        self.assertTrue(detect_repeat_incidents(alerts,cases).empty)
        cases['entity_id']='OTHER'
        self.assertTrue(detect_repeat_incidents(alerts,cases).empty)

    def test_r009_evidence_scoping(self):
        a=pd.DataFrame([dict(entity_id='E1',case_id='C',reason='copied notes')])
        b=pd.DataFrame([dict(entity_id='E2',case_id='C',reason='short duration')])
        self.assertTrue(detect_combined_suspicious_behaviour(a,b,None).empty)
        b['entity_id']='E1'
        result=detect_combined_suspicious_behaviour(a,b,None).iloc[0]
        self.assertEqual(result['rule_count'],2)
        self.assertEqual(set(result['evidence']),{'R006','R007'})
        self.assertIn('copied notes',result['reason'])

    def test_empty_frames_and_parameter_validation(self):
        inv,cases,alerts=dataset()
        self.assertTrue(all(frame.empty for frame in analyze_behaviour(inv.iloc[:0],cases.iloc[:0],alerts.iloc[:0]).values()))
        with self.assertRaises(ValueError):detect_repetitive_investigations(inv,cases_df=cases,minimum_cases=1)
        with self.assertRaises(ValueError):detect_repeat_incidents(alerts,cases,minimum_incidents=1)
        with self.assertRaises(ValueError):detect_duration_anomalies(inv,cases,alerts,maximum_deviation_ratio=1)

    def test_evaluation_never_aliases_r004_to_r007(self):
        inv,cases,alerts=dataset()
        truth=pd.DataFrame([dict(problem_type='FAST_CRITICAL_CLOSURE',expected_detection=True,case_id='C6',asset_id=None)])
        result=evaluate_rule('R007',detect_duration_anomalies(inv,cases,alerts),truth,cases,alerts)
        self.assertEqual(result['status'],'NOT_LABELLED')
        self.assertNotIn('recall',result)

    def test_asset_labels_and_false_negative_not_removed(self):
        _,cases,alerts=dataset()
        truth=pd.DataFrame([dict(problem_type='REPEAT_INCIDENT',expected_detection=True,case_id=None,asset_id='AS1')])
        result=evaluate_rule('R008',detect_repeat_incidents(alerts,cases),truth,cases,alerts)
        self.assertEqual((result['TP'],result['FP'],result['FN']),(1,0,0))
        truth=pd.DataFrame([dict(problem_type='REPETITIVE_INVESTIGATION',expected_detection=True,case_id='NO_INV',asset_id=None)])
        result=evaluate_rule('R006',pd.DataFrame(),truth,cases,alerts)
        self.assertEqual(result['FN'],1)

if __name__=='__main__':unittest.main()
