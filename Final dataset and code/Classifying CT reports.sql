WITH ct_head_notes AS (
  SELECT
    r.subject_id,
    r.hadm_id,
    r.note_id,
    r.charttime,
    rd.field_value AS ct_type,
    r.text AS full_report_text,

    CASE
      WHEN REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}(no acute intracranial|no acute abnormality|no intracranial|unremarkable|no acute process|no acute finding|no evidence of acute|no ct evidence|normal head ct|normal study|no acute traumatic|no hemorrhage|no fracture|no evidence of hemorrhage|no evidence of intracranial|without acute intracranial|without evidence of acute|without intracranial hemorrhage|without acute process|chronic small vessel|chronic lacunar|resolution of)')
      THEN 'Negative'

      WHEN REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}(hemorrhage|hematoma|infarct|fracture|mass effect|midline shift|edema|hydrocephalus|abscess|tumor|bleed|pneumocephalus|hypoxic brain|ischemi)')
      AND NOT REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}(no |without |chronic |old |prior |resolved )(acute |evidence of |intracranial )?(hemorrhage|hematoma|fracture|edema|bleed|infarct)')
      THEN 'Positive'

      WHEN REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}(post.surgical|post-surgical|postoperative|unchanged from prior|status post|craniotomy|surgical changes)')
      THEN 'Post-surgical/Unchanged'

      ELSE 'Unclear'
    END AS ct_classification,

    CASE
      WHEN REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}(hemorrhage|hematoma|bleed)') THEN 'Hemorrhage'
      WHEN REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}(infarct|ischemi)') THEN 'Infarct'
      WHEN REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}fracture') THEN 'Fracture'
      WHEN REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}(mass effect|midline shift|herniation)') THEN 'Mass Effect'
      WHEN REGEXP_CONTAINS(r.text, r'(?i)(IMPRESSION|FINDINGS)[\s\S]{0,800}hydrocephalus') THEN 'Hydrocephalus'
      ELSE NULL
    END AS positive_subtype,

    ROW_NUMBER() OVER (
      PARTITION BY r.subject_id, r.hadm_id
      ORDER BY r.charttime ASC
    ) AS ct_sequence_number

  FROM physionet-data.mimiciv_note.radiology r
  JOIN physionet-data.mimiciv_note.radiology_detail rd
    ON r.note_id = rd.note_id
  WHERE rd.field_value IN (
    'CT HEAD W/O CONTRAST',
    'CT HEAD W/ & W/O CONTRAST',
    'CT HEAD W/ CONTRAST'
  )
  AND r.hadm_id IS NOT NULL
)
SELECT
  ct_classification,
  COUNT(*) AS n,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percent
FROM ct_head_notes
GROUP BY ct_classification
ORDER BY n DESC;