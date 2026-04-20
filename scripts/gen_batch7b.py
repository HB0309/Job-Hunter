import json

results = []

# Correction batch — false negatives from batch7 (Workday Intel jobs explicitly designed
# for new graduates that were bulk-rejected because their titles had no level indicator).

results.append({
    'raw_job_id': 49890,
    'keep_in_db': True,
    'fit_score': 68,
    'fit_label': 'good_fit',
    'early_talent': True,
    'seniority': 'new_grad',
    'role_family': 'software_engineer',
    'reasoning_summary': (
        'Intel Linux/Android Kernel Engineer (entry-level / new grad). Explicitly designed for '
        'fresh graduates — "Are you a graduate... designed for graduates ready to launch their '
        'careers." Min qual: BS/MS in CS/CE + 3 months experience (internships/academic count). '
        'Folsom CA. Strong systems/kernel role — excellent for Linux, embedded systems, OS '
        'fundamentals background. No immigration sponsorship. Unique opportunity in professional '
        'kernel dev at Intel SoC platform team.'
    ),
    'ats_keywords': ['Linux kernel', 'Android kernel', 'embedded systems', 'C/C++', 'SoC', 'FPGA', 'device drivers', 'kernel modules', 'cross-compilation', 'Git'],
    'matched_skills': ['Linux', 'C/C++', 'operating systems', 'embedded systems', 'Git', 'computer architecture'],
    'missing_skills': ['FPGA experience', 'Android kernel development', 'SoC hardware', 'cross-compilation toolchains'],
    'title': 'Linux Kernel Engineer',
    'company': 'intel',
    'location': 'US, California, Folsom',
    'url': 'https://intel.wd1.myworkdayjobs.com/job/US-California-Folsom/Linux-Kernel-Engineer_JR0282647',
})

with open('/app/scripts/batch7b_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Generated {len(results)} records ({sum(1 for r in results if r['keep_in_db'])} keeps, {sum(1 for r in results if not r['keep_in_db'])} rejects)")
