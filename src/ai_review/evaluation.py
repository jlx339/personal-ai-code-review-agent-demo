"""Score real reports against independently labeled issues and human judgments."""


def evaluate(report,expected,labels):
    eligible=[f for f in report.findings if f.verification_status=='supported']
    expected_map={x['id']:x for x in expected}
    if len(expected_map)!=len(expected):
        raise ValueError('Expected issue IDs must be unique')
    judgments=[]
    matched=set()
    unlabeled=[]
    for f in eligible:
        label=labels.get(f.id)
        if label is None:
            unlabeled.append(f.id)
            continue
        if type(label.get('actionable')) is not bool:
            raise ValueError('Human actionable judgment must be boolean')
        issue=label.get('expected_id')
        if issue and issue not in expected_map:
            raise ValueError('Human match references unknown expected issue')
        judgments.append(label['actionable'])
        if issue and label['actionable']:
            matched.add(issue)
    high={k for k,v in expected_map.items() if v['severity'] in ('high','critical')}
    return dict(total_supported=len(eligible),human_labeled=len(judgments),
        actionable_precision=sum(judgments)/len(judgments) if judgments and not unlabeled else None,
        high_critical_recall=len(matched & high)/len(high) if high else None,
        missed_issue_ids=sorted(set(expected_map)-matched),unlabeled_finding_ids=unlabeled,
        false_positive_count=sum(not x for x in judgments),requests=report.usage.get('requests'),
        elapsed_seconds=report.usage.get('elapsed_seconds'))
