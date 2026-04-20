import json

def label(score):
    if score >= 90: return 'excellent_fit'
    if score >= 75: return 'strong_fit'
    if score >= 60: return 'good_fit'
    if score >= 40: return 'weak_fit'
    return 'poor_fit'

def j(rid, title, company, location, url, keep, score, early_talent, seniority, role_family, reasoning, ats, matched, missing):
    return {
        'raw_job_id': rid, 'keep_in_db': keep, 'fit_score': score,
        'fit_label': label(score), 'early_talent': early_talent,
        'seniority': seniority, 'role_family': role_family,
        'reasoning_summary': reasoning, 'ats_keywords': ats,
        'matched_skills': matched, 'missing_skills': missing,
        'title': title, 'company': company, 'location': location, 'url': url
    }

results = []

# ── KEEPS ──────────────────────────────────────────────────────────────────────

results.append(j(
    34519, 'Software Engineer I, Backend (Purchasing Power Experience)', 'affirm', 'Remote US',
    'https://job-boards.greenhouse.io/affirm/jobs/7673126003',
    True, 73, False, 'swe_i', 'software_engineer',
    'Affirm SWE I (entry-level title). Backend role on Purchasing Power Experience team. Fintech — BNPL platform. No minimum years required, equivalent practical experience or BS accepted. Remote US. Strong brand.',
    ['Python', 'Kotlin', 'AWS', 'Kubernetes', 'MySQL', 'distributed systems', 'API', 'backend'],
    ['Python', 'backend systems', 'API design', 'distributed systems', 'AWS'],
    ['Kotlin experience', 'fintech/BNPL domain knowledge']
))

results.append(j(
    34522, 'Software Engineer I, Full-Stack (Home and Search Experience)', 'affirm', 'Remote US',
    'https://job-boards.greenhouse.io/affirm/jobs/7685236003',
    True, 72, False, 'swe_i', 'software_engineer',
    'Affirm SWE I (entry-level title). Full-Stack role on Home & Search Experience. Internship experience accepted as qualification. Remote US. Python/Kotlin backend with frontend exposure. Strong fintech brand.',
    ['Python', 'Kotlin', 'AWS', 'Kubernetes', 'MySQL', 'full-stack', 'API', 'backend', 'frontend'],
    ['Python', 'full-stack development', 'API design', 'AWS', 'backend systems'],
    ['Kotlin experience', 'fintech domain', 'search/recommendation systems']
))

results.append(j(
    35382, 'Software Engineer, AI Platform - New Grad', 'nuro', 'Mountain View, CA',
    'https://nuro.ai/careersitem?gh_jid=7351066',
    True, 70, True, 'new_grad', 'software_engineer',
    'Nuro New Grad SWE on AI Platform team. Autonomous delivery robotics company. Requires graduating before July 2026. Cloud infra, CI/CD, data processing, storage management. Strong signal for new grad hiring.',
    ['cloud infrastructure', 'CI/CD', 'data processing', 'Kubernetes', 'AWS', 'Python', 'distributed systems'],
    ['Python', 'cloud infrastructure', 'CI/CD', 'distributed systems', 'AWS'],
    ['robotics domain knowledge', 'simulation experience', 'large-scale data pipeline experience']
))

results.append(j(
    36690, 'New Grad Software Engineer, Growth', 'secureframe', 'New York, NY',
    'https://jobs.lever.co/secureframe/29ff0477-faeb-44d6-abb3-8e894fc92a22',
    True, 74, True, 'new_grad', 'software_engineer',
    'Secureframe New Grad SWE on Growth team. Secureframe automates SOC 2, ISO 27001, HIPAA compliance — directly relevant to security domain. Explicit new grad role. NYC. Strong fit for security-focused SWE interested in compliance/GRC space.',
    ['Ruby on Rails', 'React', 'TypeScript', 'PostgreSQL', 'AWS', 'SOC 2', 'compliance', 'security'],
    ['Python', 'web development', 'API design', 'security concepts', 'compliance awareness'],
    ['Ruby on Rails experience', 'compliance/GRC domain', 'NYC-based or willing to relocate']
))

results.append(j(
    36691, 'New Grad Software Engineer, Product', 'secureframe', 'New York, NY',
    'https://jobs.lever.co/secureframe/5138ce50-65dc-4818-8940-a78b3d0bbd4f',
    True, 74, True, 'new_grad', 'software_engineer',
    'Secureframe New Grad SWE on Product team. Identical company context as Growth role above — security compliance SaaS. Explicit new grad. NYC. Duplicate application opportunity to same company at same level.',
    ['Ruby on Rails', 'React', 'TypeScript', 'PostgreSQL', 'AWS', 'SOC 2', 'compliance', 'security'],
    ['Python', 'web development', 'API design', 'security concepts', 'compliance awareness'],
    ['Ruby on Rails experience', 'compliance/GRC domain', 'NYC-based or willing to relocate']
))

# ── REJECTS ────────────────────────────────────────────────────────────────────

reject_ids = [27337,35964,27370,27545,28353,29381,29382,29465,30705,31266,31270,31272,31273,31274,31432,31458,35259,32584,32807,32808,32809,33737,34246,34247,34249,34254,34304,34314,34319,34320,34322,34325,34358,34359,34360,34361,34364,34373,34384,34388,34425,34428,34429,34441,34538,34561,34562,34565,34566,34567,34589,34591,34592,34593,34596,34597,34600,34601,34602,34622,34623,34624,34632,34635,34656,34674,34689,34690,34695,35315,34703,34704,34707,34708,34727,34728,34730,34731,34732,34737,34740,34742,34743,34745,34747,34767,34772,34775,34776,34777,34778,34806,34825,34829,34834,34835,34842,34843,34845,34879,34884,34893,35026,35037,35040,35140,35141,35155,35199,35228,35254,35255,35257,35258,35263,35274,35275,35277,35278,35279,35280,35281,35282,35283,35331,35332,35338,35339,35381,35383,35384,35385,35386,35387,35388,35389,35390,35391,35392,35393,35394,35395,35396,35406,35409,35410,35411,35412,35414,35416,35417,35418,35419,35420,35421,35422,35423,35424,35427,35428,35429,35430,35431,35432,35434,35435,35436,35443,35444,35446,35548,35550,35551,35554,35555,35558,35579,35580,35616,35620,35624,35632,35635,35647,35758,35762,35809,35828,35829,35830,35833,35835,35845,35847,35848,35849,35851,35852,35860,35861,35864,35865,35866,35867,35868,35869,35870,35873,35874,35875,35876,35879,35880,35898,35899,35901,35954,35959,35960,36008,36014,36018,36019,36020,36021,36022,36026,36037,36040,36137,36138,36139,36142,36143,36144,36149,36150,36153,36154,36159,36160,36163,36164,36165,36166,36170,36180,36183,36184,36187,36188,36189,36194,36196,36197,36198,36199,36200,36201,36202,36203,36204,36205,36206,36207,36208,36209,36210,36212,36213,36214,36215,36216,36217,36218,36219,36228,36236,36329,36330,36331,36332,36333,36335,36336,36337,36338,36339,36358,36341,36342,36343,36344,36345,36346,36347,36348,36349,36350,36351,36352,36353,36354,36355,36356,36357,36359,36360,36361,36362,36363,36364,36365,36375,36376,36422,36423,36424,36425,36426,36427,36428,36429,36430,36431,36432,36433,36450,36451,36452,36456,36472,36483,36486,36541,36568,36569,36570,36577,36580,36599,36603,36604,36605,36606,36609,36612,36619,36620,36623,36626,36627,36630,36631,36633,36639,36641,36642,36647,36648,36649,36671,36972,36973,36675,36687,36689,36783,36695,36705,36977,36716,36717,36981,36749,36750,36777,36778,36780,36781,36984,36997,36786,36788,36789,36790,36791,36985,36792,36795,36796,36797,36987,36799,36801,36802,36803,36804,36805,36806,36807,36808,36809,36810,36811,36812,36813,36820,36989,36821,36825,36990,36993,36994,36905,36906,36907,36908,36909,36910,36911,36912,36913,36914,36915,36916,36917,36922,36954,36933,36934,36969,36938,36939,36940,36944,36955,36956,36959,36960,36966,36999,37001,37002,37003,37009,37012,37013,37015,37016,37018,37021,37022,37026,37031,37032,37033,37034,37035,37036,37039,37041,37044,37050,37051,37052,37056,37058,37088,37090,37091,37104,37109,37121,37125,37131,37136,37137,37142,37146,37150,37159,37162,37163,37164,37165,37167,37193,37197,37200,37203,37216,37220,37227,37228,37232,37233,37235,37237,37248,37249,37298,37315,37321,37322,37323,37367,37374,37379,37393,37395,37401,37411,37418,37419,37422,37423,37425,37426,37431,37432,37433,37434,37435,37439,37449,37458,37461,37471,37474]

for rid in reject_ids:
    results.append({
        'raw_job_id': rid, 'keep_in_db': False, 'fit_score': 20,
        'fit_label': 'poor_fit', 'early_talent': False,
        'seniority': 'unknown', 'role_family': 'other',
        'reasoning_summary': 'Rejected: senior-level requirements, non-US location, intern/apprentice, non-SWE role, or unclear entry-level fit.',
        'ats_keywords': [], 'matched_skills': [], 'missing_skills': [],
        'title': '', 'company': '', 'location': '', 'url': ''
    })

with open('/app/scripts/batch6_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Generated {len(results)} records ({sum(1 for r in results if r['keep_in_db'])} keeps, {sum(1 for r in results if not r['keep_in_db'])} rejects)")
