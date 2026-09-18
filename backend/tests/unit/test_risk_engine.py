"""Pure deterministic risk contracts; no operational database writes."""
import copy
import math
import unittest
from app.core.risk_config import DEFAULT_CONFIG, risk_config, level
from app.services.risk.finding_aggregator import ENGINES, normalize_findings, workflow_findings
from app.services.risk.risk_engine import calculate_risk
from app.services.risk.prioritization import prioritize_cases
from app.services.risk.benchmark_engine import benchmark_entity

ENTITY=dict(entity_id='X',entity_name='Test',sector='Banking',peer_group='Banking')

def exposure(n=10):
    cases={f'C{i}' for i in range(n)}
    return dict(cases=cases,serious_cases=cases,critical_cases=cases,investigated_cases=cases,
                investigated_serious_cases=cases,monitored_assets={'A0'} if n else set())

def finding(rule='R003',case='C0',**changes):
    result=dict(entity_id='X',rule_id=rule,case_id=case,asset_id='A0',severity='CRITICAL',
                assessment='CONFIRMED_GAP',source='rule_engine',problem_type='TEST',reason='Source evidence',evidence={})
    result.update(changes)
    return result

class RiskTests(unittest.TestCase):
    def test_no_findings(self):
        r=calculate_risk(ENTITY,[],exposure())
        self.assertEqual((r['overall_score'],r['overall_level']),(0,'LOW'))
        self.assertEqual(r['aggregation']['total_findings'],0)

    def test_single_finding_formula(self):
        r=calculate_risk(ENTITY,[finding()],exposure())
        self.assertEqual(r['components']['EXECUTION_GAP_RISK']['score'],10)
        self.assertEqual(r['overall_score'],3)
        self.assertEqual(r['metrics']['missing_escalation_rate']['value'],10)

    def test_multiple_categories(self):
        rows=[finding(),finding('R005',None,source='negative_space_engine'),finding('R006',source='behaviour_analytics')]
        r=calculate_risk(ENTITY,rows,exposure())
        self.assertEqual(r['overall_score'],25)
        self.assertEqual(r['aggregation']['negative_space_count'],1)
        self.assertEqual(r['aggregation']['behaviour_analytics_count'],1)

    def test_duplicates_do_not_inflate(self):
        rows=[finding(finding_id='1'),finding(finding_id='2')]
        r=calculate_risk(ENTITY,rows,exposure())
        self.assertEqual(r['aggregation']['total_findings'],1)
        self.assertEqual(r['overall_score'],3)
        self.assertEqual(r['findings'][0]['source_finding_ids'],['1','2'])

    def test_repeated_category_caps_per_case(self):
        rows=[finding('R006',source='behaviour_analytics',evidence={'record':i}) for i in range(100)]
        rows.append(finding('R009',source='behaviour_analytics'))
        self.assertEqual(calculate_risk(ENTITY,rows,exposure())['overall_score'],2)

    def test_zero_denominators(self):
        r=calculate_risk(ENTITY,[],exposure(0))
        self.assertEqual(r['overall_score'],0)
        self.assertEqual(r['score_status'],'PARTIAL')
        self.assertIsNone(r['metrics']['missing_escalation_rate']['value'])
        self.assertEqual(r['unavailable_component_upper_bound'],100)

    def test_missing_optional_values(self):
        r=calculate_risk(ENTITY,[finding(asset_id=None)],dict(cases={'C0'}))
        self.assertTrue(math.isfinite(r['overall_score']))
        self.assertTrue(r['components']['EXECUTION_GAP_RISK']['excluded_finding_ids'])
        self.assertIsNone(r['metrics']['median_investigation_minutes']['value'])

    def test_score_bounds(self):
        rows=[finding(rule,source=source) for rule,source in [('R003','rule_engine'),('R005','negative_space_engine'),
            ('R006','behaviour_analytics'),('R008','behaviour_analytics'),('C001','contradiction_engine')]]
        self.assertEqual(calculate_risk(ENTITY,rows*50,exposure(1))['overall_score'],100)
        self.assertGreaterEqual(calculate_risk(ENTITY,[],exposure(1))['overall_score'],0)

    def test_level_boundaries(self):
        config=risk_config()
        for value,expected in [(0,'LOW'),(24.99,'LOW'),(25,'MODERATE'),(49.99,'MODERATE'),(50,'HIGH'),(75,'CRITICAL'),(100,'CRITICAL')]:
            self.assertEqual(level(value,config),expected)
        for value in [-1,101,float('nan')]:
            with self.assertRaises(ValueError):level(value,config)

    def test_configuration_validation(self):
        for key,member,value in [('component_weights','EXECUTION_GAP_RISK',-.3),('severity_weights','HIGH',float('nan')),
                                  ('severity_weights','HIGH',2),('level_thresholds','HIGH',10)]:
            config=copy.deepcopy(DEFAULT_CONFIG);config[key][member]=value
            with self.assertRaises(ValueError):risk_config(config)

    def test_priority_explanation_and_multiple_cases(self):
        rows=normalize_findings([finding(),finding('R006',source='behaviour_analytics')])
        cases=[dict(entity_id='X',case_id='C0',severity='CRITICAL',asset_criticality='HIGH'),
               dict(entity_id='X',case_id='C1',severity='LOW',asset_criticality=None)]
        ranked=prioritize_cases(cases,rows)
        self.assertEqual(ranked[0]['priority_score'],81)
        self.assertEqual(ranked[1]['priority_score'],5)
        self.assertIn('Source evidence',ranked[0]['reason'])
        self.assertIn('No findings',ranked[1]['reason'])
        self.assertEqual(ranked,prioritize_cases(cases[::-1],rows*10))

    def test_priority_cap(self):
        rows=normalize_findings([finding(rule) for rule in ['R003','R006','R008','C001']])
        case=dict(entity_id='X',case_id='C0',severity='CRITICAL',asset_criticality='CRITICAL')
        self.assertEqual(prioritize_cases([case],rows)[0]['priority_score'],100)

    def test_insufficient_data_not_scored(self):
        r=calculate_risk(ENTITY,[finding(assessment='INSUFFICIENT_DATA')],exposure())
        self.assertEqual(r['overall_score'],0)
        self.assertEqual(r['aggregation']['total_findings'],1)
        self.assertEqual(r['metrics']['missing_escalation_rate']['numerator'],0)

    def test_missing_engine_not_zero(self):
        statuses={e:'AVAILABLE' for e in ENGINES if e!='behaviour_analytics'}
        r=calculate_risk(ENTITY,[],exposure(),statuses)
        self.assertIsNone(r['components']['INVESTIGATION_QUALITY_RISK']['score'])
        self.assertIsNone(r['metrics']['repetitive_investigation_rate']['value'])
        self.assertEqual(r['available_component_weight'],.65)

    def test_cross_entity_rejected(self):
        with self.assertRaises(ValueError):calculate_risk(ENTITY,[finding(entity_id='Y')],exposure())

    def test_invalid_findings_not_silently_dropped(self):
        for changes in [dict(severity=None),dict(assessment=None),dict(evidence='text'),dict(reason='')]:
            with self.assertRaises(ValueError):normalize_findings([finding(**changes)])

    def test_size_normalization(self):
        a=calculate_risk(ENTITY,[finding()],exposure(10))
        b=calculate_risk(ENTITY,[finding(case='C0'),finding(case='C1')],exposure(20))
        self.assertEqual(a['overall_score'],b['overall_score'])

    def test_workflow_overlap(self):
        audit=dict(entity_id='X',case_id='C0',asset_id='A0',alert_id='L',severity='HIGH',records={},
            gaps=[dict(rule_id='R003',stage='ESCALATION',reason='same'),dict(rule_id=None,stage='EVIDENCE',reason='auditor')])
        rows=workflow_findings([audit],[finding()])
        self.assertEqual([r['rule_id'] for r in rows],['WF_EVIDENCE'])

    def test_banking_peers_and_leave_one_out(self):
        a=calculate_risk(ENTITY,[finding()],exposure(10))
        b=calculate_risk(dict(ENTITY,entity_id='Y'),[],exposure(10))
        c=calculate_risk(dict(ENTITY,entity_id='Z',peer_group=None),[],exposure(10))
        result=benchmark_entity(a,[a,b,c])
        self.assertEqual(result['peer_entity_ids'],['Y','Z'])
        self.assertEqual(result['metrics']['missing_escalation_rate']['peer_median'],0)
        self.assertEqual(result['metrics']['missing_escalation_rate']['description'],'above peer median')
        self.assertEqual(benchmark_entity(c,[a,b,c])['peer_group_source'],'configured_sector_fallback')

    def test_different_sector_or_group_excluded(self):
        a=calculate_risk(ENTITY,[],exposure())
        b=calculate_risk(dict(ENTITY,entity_id='Y',sector='Telecom'),[],exposure())
        c=calculate_risk(dict(ENTITY,entity_id='Z',peer_group='Different'),[],exposure())
        self.assertEqual(benchmark_entity(a,[a,b,c])['peer_entity_ids'],[])

    def test_no_peers_and_zero_peer_denominator(self):
        a=calculate_risk(ENTITY,[],exposure())
        b=calculate_risk(dict(ENTITY,entity_id='Y'),[],exposure(0))
        self.assertEqual(benchmark_entity(a,[a])['status'],'NO_VALID_PEERS')
        value=benchmark_entity(a,[a,b])['metrics']['missing_escalation_rate']
        self.assertEqual(value['status'],'NO_VALID_PEERS')
        self.assertIsNone(value['peer_median'])

    def test_fallback_can_be_disabled(self):
        a=calculate_risk(dict(ENTITY,peer_group=None),[],exposure())
        b=calculate_risk(dict(ENTITY,entity_id='Y'),[],exposure())
        config=copy.deepcopy(DEFAULT_CONFIG);config['peer_group_fallbacks']={}
        self.assertEqual(benchmark_entity(a,[a,b],config)['status'],'NO_VALID_PEERS')

    def test_determinism(self):
        rows=[finding(),finding('R006',source='behaviour_analytics')]
        self.assertEqual(calculate_risk(ENTITY,rows,exposure()),calculate_risk(ENTITY,rows[::-1],exposure()))

if __name__=='__main__':unittest.main()
