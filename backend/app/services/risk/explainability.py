"""Deterministic supervisory handoff; no external generation service."""

def supervisory_summary(risk, peer_context, priority_cases, limit=5):
    return dict(entity_id=risk['entity_id'],entity_name=risk['entity_name'],
        overall_score=risk['overall_score'],risk_level=risk['overall_level'],score_status=risk['score_status'],
        components=risk['components'],top_contributors=risk['top_contributors'][:limit],
        explanation=risk['explanation'],peer_context=peer_context,priority_cases=priority_cases[:limit],
        limitations=risk['limitations'],disclaimer=risk['disclaimer'])
