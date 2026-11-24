// Deaths in one study. Event flags are 1 or 0 when the dictionary label is
// Yes/Event/Dead or No/Censor. Other labels stay as the raw code.
MATCH (p:Patient {study_id: 'P-5370'})-[v:HAS_VALUE]->(:Field {field_id: 'overall_survival.event'})
WHERE v.value_num = 1
RETURN count(p) AS deaths;

// Mean recipient age, using the continuous field rather than the study-specific bins.
MATCH (p:Patient)-[v:HAS_VALUE]->(:Field {field_id: 'recipient_age.measure'})
RETURN p.study_id AS study_id, avg(v.value_num) AS mean_age, count(p) AS patients
ORDER BY patients DESC;

// Studies that recorded non-relapse mortality.
MATCH (s:Study)<-[:ENROLLED_IN]-(:Patient)-[:HAS_VALUE]->(:Field {field_id: 'nrm.event'})
RETURN DISTINCT s.study_id AS study_id, s.title AS title
ORDER BY study_id;

// Survival time is months. Day clocks were converted; an unspecified unit is left as reported.
MATCH (p:Patient)-[t:HAS_VALUE]->(:Field {field_id: 'overall_survival.time'})
WHERE t.unit = 'months' AND t.value_num > 12
RETURN p.study_id, count(p) AS followed_past_one_year
ORDER BY followed_past_one_year DESC;

// Sex by label, so 1=Male in one study and a different integer in another still match.
MATCH (p:Patient)-[v:HAS_VALUE]->(:Field {field_id: 'recipient_sex.category'})
RETURN v.value_text AS sex, count(p) AS patients
ORDER BY patients DESC;
