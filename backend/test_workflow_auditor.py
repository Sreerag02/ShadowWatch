"""Readable DB report. Defaults to E001-C0081; supports --case or --entity."""

import argparse

from services.workflow_auditor import audit_case_workflow, audit_entity_workflows


def print_assessment(result):
    print(f"\nCase: {result['case_id']}\nSeverity: {result['severity']}\nCategory: {result['category']}")
    print('\nEXPECTED VS OBSERVED (prototype)')
    for stage, expected in result['expected'].items():
        observed = result['observed'][stage]
        expected_label = 'Required' if expected else 'No policy'
        if stage == 'closure':
            expected_label = 'No deadline'
        observed_label = {True: 'Present', False: 'Absent', None: 'Unknown/mixed'}[observed]
        print(f'{stage.capitalize():16} Expected: {expected_label:10} Observed: {observed_label}')
    duration = result['closure_minutes']
    print(f'\nClosure Time: {duration:.1f} minutes' if duration is not None else '\nClosure Time: Unknown')
    if result['closure_policy']:
        print(f"Prototype timing check: below {result['closure_policy']['minimum_minutes']} minutes triggers R004")
    print('\nConfirmed Execution Gaps:')
    for gap in result['gaps']:
        print(f"- {gap['rule_id'] or 'Prototype'} {gap['reason']}")
    if not result['gaps']:
        print('- None established from available records')
    print('\nInsufficient Data:')
    for issue in result['data_issues']:
        print(f"- {issue['stage']} ({issue['source_id']}): {issue['reason']}")
    if not result['data_issues']:
        print('- No unresolved required checks')
    print('\nRule-engine triggers (not all are confirmed gaps):', ', '.join(result['triggered_rules']) or 'None')
    print('Required checks complete:', 'Yes' if result['assessment_complete'] else 'No')
    print('\nAssessment:', result['assessment'])
    print('\n' + result['explanation'])
    print('\nLimitations:')
    for limitation in result['limitations']:
        print('-', limitation)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--case', default='E001-C0081')
    group.add_argument('--entity')
    args = parser.parse_args()
    print('========================================\n SHADOWWATCH WORKFLOW AUDITOR\n========================================')
    if args.entity:
        results = audit_entity_workflows(args.entity)
        print('Cases assessed:', len(results))
    else:
        result = audit_case_workflow(args.case)
        results = [result] if result else []
        if result is None:
            print('Case not found:', args.case)
    for result in results:
        print_assessment(result)
    print('\n========================================\n ANALYSIS COMPLETE\n========================================')


if __name__ == '__main__':
    main()
