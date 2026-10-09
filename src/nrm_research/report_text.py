"""
Role: Text content of the survival workflow report.
Description: The report is a tuple of title, subtitle and blocks, in the
shape that report_pdf.write_report takes. Numbers come from the converted
starting_point files on 2026-10-09 and carry their denominators.
Author: Bor
"""

CM = 28.35

OVERALL_SURVIVAL = (
    'Workflow for predicting overall survival after stem cell transplant',
    'Plan saved 2026-10-09. Data: six studies in data/starting_point.',
    [
        ('h1', 'Status of this report'),
        ('table', [
            ['Item', 'Status'],
            ['Modelling code', 'Not written or run. This report is a plan.'],
            ['Counts', 'Read from the data files on 2026-10-09.'],
            ['Variable mapping across studies',
             'Inferred from column names, not yet checked against each '
             'dictionary.'],
        ], [5 * CM, 11 * CM]),
        ('h1', 'How overall survival differs from NRM'),
        ('table', [
            ['', 'NRM', 'Overall survival'],
            ['Event', 'trm = 1', 'dead = 1'],
            ['Time', 'intxrel or intxsurv', 'intxsurv for every patient'],
            ['Competing risk', 'Relapse competes',
             'None. Death is the only event and survivors are censored'],
            ['Missing values', 'Some trm is NaN or 99',
             'None in dead across the six studies'],
        ], [3.5 * CM, 5.5 * CM, 7 * CM]),
        ('bullets', [
            'The six studies have 30,106 patients and 15,954 deaths '
            '(dead = 1 summed over the studies). That is about 2.4 times '
            'the events available for NRM.',
            'Standard right censored survival methods apply. Fine Gray and '
            'cumulative incidence are not needed.',
            'All studies use months. P-5646 intxsurv is also in months. '
            'Only its intxrel_d is in days.',
        ]),
        ('h1', 'Workflow'),
        ('numbered', [
            '<b>Build the table.</b> Read the six CSVs from '
            'results/processed/sas_files. Keep dead and intxsurv. Drop rows '
            'with a missing or non positive time. Add study and disease '
            'group columns.',
            '<b>Pick predictors known at transplant.</b> Use the same list '
            'as for NRM: age, sex, KPS, HCT-CI, disease status, '
            'cytogenetics, donor type, graft type, conditioning, '
            'serotherapy, GVHD prophylaxis and transplant year. Exclude '
            'everything after transplant: rel, trm, dfs, grfs, GVHD, '
            'engraftment, infection columns and the intx* columns other '
            'than intxsurv. Using rel or trm would leak the answer, '
            'because relapse and TRM are causes of death.',
            '<b>Harmonise.</b> Use the mapping table in the starting_point '
            'NRM report. Confirm each mapping against its dictionary '
            'first. A variable absent in a study becomes missing with an '
            'indicator column.',
            '<b>Split.</b> Main test: leave one study out, six folds. Add '
            'cross validation grouped by centre inside the training '
            'studies, and a temporal split on transplant year. Fit '
            'imputation and scaling inside each training fold only. The '
            'same patient may appear in more than one study and cannot be '
            'detected, so state that as a limit.',
            '<b>Baselines.</b> Cox with elastic net, stratified by study '
            'or with study as a covariate. Also a Weibull accelerated '
            'failure time model. Every other model has to beat these.',
            '<b>Machine learning.</b> Random survival forest and a '
            'gradient boosted survival model (XGBoost Cox or AFT). Then a '
            'neural network: DeepSurv as the simple option, and a discrete '
            'time network such as DeepHit or Logistic Hazard as the '
            'second, with a study embedding, dropout, weight decay and '
            'early stopping. Tune on inner folds only.',
            '<b>Evaluate.</b> C index, integrated Brier score and time '
            'dependent AUC at 1, 2 and 5 years. Calibration plots of '
            'predicted against Kaplan Meier survival by risk group. Report '
            'by held out study and by subgroup (age group, donor type, '
            'conditioning intensity), with bootstrap confidence intervals '
            'and the number of deaths behind each figure.',
            '<b>Explain.</b> SHAP or permutation importance. Check that '
            'the top variables make clinical sense. Age, HCT-CI, KPS, '
            'disease status and donor type are the expected ones.',
        ]),
        ('h1', 'Cautions'),
        ('bullets', [
            'Follow up differs. The median is 13 to 25 months across '
            'studies. Five year estimates rest on fewer patients, and '
            'differences between studies may reflect study design as much '
            'as patients.',
            'Each study had its own inclusion rules. A model that leans on '
            'the study indicator will not transfer. Compare results with '
            'and without it.',
            'Overall survival combines relapse, NRM and other deaths. The '
            'NRM model is more specific. An OS model that predicts well '
            'may be tracking relapse risk, which the clinical question '
            'may not need. State which question the model answers before '
            'building it.',
        ]),
    ],
)
