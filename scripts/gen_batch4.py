import json

def score_to_label(score):
    if score >= 90: return 'excellent_fit'
    if score >= 75: return 'strong_fit'
    if score >= 60: return 'good_fit'
    if score >= 40: return 'weak_fit'
    return 'poor_fit'

def j(raw_job_id, title, company, location, url, keep, score, early_talent, seniority, role_family, reasoning, ats, matched, missing):
    return {
        'raw_job_id': raw_job_id, 'keep_in_db': keep, 'fit_score': score,
        'fit_label': score_to_label(score), 'early_talent': early_talent,
        'seniority': seniority, 'role_family': role_family,
        'reasoning_summary': reasoning, 'ats_keywords': ats,
        'matched_skills': matched, 'missing_skills': missing,
        'title': title, 'company': company, 'location': location, 'url': url
    }

results = []

# ── KEEPS ──────────────────────────────────────────────────────────────────────

# Contentful AppSec x6
for rid, loc, jid in [
    (19357,'Raleigh, NC','7782201'), (19358,'Atlanta, GA','7782195'),
    (19359,'New York City, NY','7774018'), (19360,'Philadelphia, PA','7782199'),
    (19361,'Tampa, FL','7782181'), (19362,'Orlando, FL','7782161')]:
    results.append(j(rid,'Security Engineer (Application Security)','contentful',loc,
        'https://job-boards.greenhouse.io/contentful/jobs/'+jid,
        True,72,False,'mid','security_engineer',
        'AppSec role at Contentful (enterprise CMS). Application security aligns with profile: secure code review, threat modeling, OWASP, SAST/DAST. US location.',
        ['application security','AppSec','SAST','DAST','threat modeling','secure SDLC','Python','Linux'],
        ['application security','Python','Linux','Docker','secure SDLC','OWASP','threat modeling'],
        ['prior dedicated AppSec role','enterprise SaaS experience']))

# Palantir New Grad x7
for rid, title, loc, slug, score in [
    (20097,'Software Engineer, New Grad','New York, NY','94984771-0704-446c-88c6-91ce748f6d92',72),
    (20099,'Software Engineer, New Grad','Seattle, WA','dea9d3d5-75b2-4588-b7bd-585a47b79c8c',72),
    (20100,'Software Engineer, New Grad - Infrastructure','New York, NY','4abf26b4-795c-420a-bf22-1ab98db268b4',74),
    (20101,'Software Engineer, New Grad - Infrastructure','Palo Alto, CA','7d75bed5-45d8-4876-840a-2d92ea79c98d',74),
    (20103,'Software Engineer, New Grad - Production Infrastructure','Washington, D.C.','15844944-fb69-4b57-9531-e988650b20c6',74),
    (20105,'Software Engineer, New Grad - Production Infrastructure','Seattle, WA','4d5a144e-87ea-45e2-a68c-3fad590629af',74),
    (20106,'Software Engineer, New Grad - Production Infrastructure','New York, NY','e1a6c138-98bf-45e2-97f7-2c70371cc38a',74)]:
    infra = 'nfrastructure' in title
    results.append(j(rid,title,'palantir',loc,'https://jobs.lever.co/palantir/'+slug,
        True,score,True,'new_grad','software_engineer',
        'Palantir New Grad SWE. Explicit new grad. Strong company. Infrastructure focus aligns with Docker/Linux/Kafka background.' if infra
        else 'Palantir New Grad SWE. Explicit new grad. Strong brand, systems/backend work.',
        ['new grad','software engineer','Python','Linux','distributed systems','infrastructure' if infra else 'backend'],
        ['Python','Linux','Docker','Kafka' if infra else 'backend systems','GitHub Actions'],
        ['Palantir-specific stack']))

# Single keeps
results += [
    j(19291,'Software Engineer, University Grad','gleanwork','San Francisco Bay Area',
      'https://job-boards.greenhouse.io/gleanwork/jobs/4592324005',
      True,70,True,'new_grad','software_engineer',
      'Glean (AI enterprise search, Series E) University Grad SWE. Explicit new grad. Python/backend skills directly relevant.',
      ['university grad','software engineer','Python','backend','search infrastructure','distributed systems'],
      ['Python','Linux','Docker','backend systems','PostgreSQL'],
      ['Go/Rust experience','prior industry SWE role']),

    j(20261,'Full Stack Software Engineer (Early Career)','lindy','Remote',
      'https://jobs.ashbyhq.com/lindy/a5100dbe-d851-4544-bb4c-0428d77940eb',
      True,65,True,'entry_level','software_engineer',
      'Lindy (AI assistant) explicitly targets early career. Python backend overlap. Remote-first startup.',
      ['full stack','early career','Python','backend','React','PostgreSQL'],
      ['Python','backend','Docker','PostgreSQL','GitHub Actions'],
      ['React/frontend experience']),

    j(18082,'Application Security Engineer','elevenlabs','Remote',
      'https://jobs.ashbyhq.com/elevenlabs/ed322919-002e-4d1e-819a-e9336cad7a4d',
      True,65,False,'mid','security_engineer',
      'ElevenLabs AppSec Engineer, Remote. AppSec skills align: web security, vuln scanning, OWASP. Fast-growing AI audio company.',
      ['application security','AppSec','SAST','DAST','secure SDLC','Python','OWASP','vulnerability assessment'],
      ['application security','Python','Linux','OWASP','Nessus','vulnerability scanning','Metasploit'],
      ['Burp Suite','prior AppSec eng role']),

    j(18095,'Compliance Engineer - US','elevenlabs','',
      'https://jobs.ashbyhq.com/elevenlabs/f80d0420-b6e6-4110-940c-293f64b9761e',
      True,60,False,'mid','security_engineer',
      'ElevenLabs Compliance Engineer, US-designated. SOC2/ISO 27001 aligns with NIST CSF and ISO 27001 background.',
      ['compliance','SOC2','ISO 27001','GRC','security controls','risk assessment','NIST'],
      ['ISO 27001','NIST CSF','security frameworks','risk assessment'],
      ['audit experience','prior compliance eng role']),

    j(19235,'Security Engineer','runpod','Remote, USA',
      'https://job-boards.greenhouse.io/runpod/jobs/4118412008',
      True,68,False,'mid','security_engineer',
      'RunPod (GPU cloud) Security Engineer, Remote US. Cloud/infra security — Docker, Linux, Wazuh SIEM, network security all directly relevant.',
      ['security engineer','cloud security','infrastructure security','Python','Linux','Docker','SIEM','vulnerability management'],
      ['Python','Linux','Docker','Wazuh','SIEM','Nmap','Wireshark','network security','vulnerability management'],
      ['AWS/GCP certifications','cloud security role experience']),

    j(17929,'Software Engineer, Security','cohere','Remote',
      'https://jobs.ashbyhq.com/cohere/b9c8c98e-b0fa-43b6-93b0-fa780d956066',
      True,62,False,'mid','security_engineer',
      'Cohere SWE Security at LLM company. Security engineering + Python central. Remote. AI company security scope is broad.',
      ['software engineer security','Python','Linux','threat modeling','secure SDLC','cryptography','Docker'],
      ['Python','Linux','Docker','security engineering','threat modeling','secure SDLC'],
      ['AI/ML security specifics','prior security SWE role']),

    j(19264,'Security Engineer, Application Security','gleanwork','San Francisco Bay Area',
      'https://job-boards.greenhouse.io/gleanwork/jobs/4529774005',
      True,62,False,'mid','security_engineer',
      'Glean AppSec Engineer. Series E AI search company. Strong AppSec skills overlap.',
      ['application security','AppSec','SAST','DAST','Python','Linux','secure SDLC','OWASP'],
      ['application security','Python','Linux','OWASP','vulnerability scanning','secure SDLC'],
      ['prior AppSec eng role','SaaS enterprise security experience']),

    j(19265,'Security Engineer, Cloud Security','gleanwork','Remote - US',
      'https://job-boards.greenhouse.io/gleanwork/jobs/4650994005',
      True,62,False,'mid','security_engineer',
      'Glean Cloud Security Engineer, Remote US. Cloud infra security — Docker, Linux, network security all relevant.',
      ['cloud security','AWS','infrastructure security','Python','Linux','IAM','network security'],
      ['Python','Linux','Docker','network security','TCP/IP','infrastructure automation'],
      ['AWS/GCP certifications','dedicated cloud security role']),

    j(19290,'Software Engineer, Security','gleanwork','San Francisco Bay Area',
      'https://job-boards.greenhouse.io/gleanwork/jobs/4436194005',
      True,60,False,'mid','security_engineer',
      'Glean SWE Security. Python + security knowledge applicable at AI search company.',
      ['software engineer','security','Python','backend','Linux','threat modeling'],
      ['Python','Linux','Docker','security engineering'],
      ['prior dedicated security eng role']),

    j(19815,'Security Engineer','helsing','Washington, DC',
      'https://helsing.ai/jobs/4774775101?gh_jid=4774775101',
      True,62,False,'mid','security_engineer',
      'Helsing (defense AI) Security Engineer, DC. Defense-sector security. Wazuh, network security, Linux all match. DC = defense hub.',
      ['security engineer','defense','SIEM','Linux','network security','threat detection','Python'],
      ['Python','Linux','Wazuh','SIEM','Nmap','Wireshark','NIST','network security'],
      ['active security clearance','defense contractor experience']),

    j(20343,'Application Security Engineer','lovable','',
      'https://jobs.ashbyhq.com/lovable/d15f1a6a-dbba-41d6-b8b4-90fc00de183c',
      True,62,False,'mid','security_engineer',
      'Lovable (AI code gen) AppSec Engineer. SDLC security, secure code review relevant at AI coding product.',
      ['application security','AppSec','SAST','DAST','secure SDLC','Python','vulnerability assessment'],
      ['application security','Python','Linux','secure SDLC','OWASP','vulnerability assessment'],
      ['prior AppSec eng role','Burp Suite']),

    j(20363,'FullStack Engineer - Product Security','lovable','',
      'https://jobs.ashbyhq.com/lovable/1f86955c-2748-4cd6-bd69-7e5c2c3fe465',
      True,60,False,'mid','security_engineer',
      'Lovable Product Security SWE. Full-stack + security mindset — matches security+SWE background.',
      ['product security','full stack','Python','JavaScript','secure coding','AppSec'],
      ['Python','secure coding','security engineering','backend development'],
      ['frontend frameworks','product security tooling']),

    j(19918,'Product Security Engineer','plaid','New York',
      'https://jobs.lever.co/plaid/49f7e590-5487-4c58-84fb-54045ab793d1',
      True,62,False,'mid','security_engineer',
      'Plaid fintech Product Security Engineer, NY. Fintech security + Python + secure SDLC all align.',
      ['product security','fintech security','Python','secure SDLC','threat modeling','API security'],
      ['Python','security engineering','threat modeling','Linux','Docker','API security'],
      ['fintech domain knowledge','prior product security role']),

    j(19277,'Software Engineer, AI & Security','gleanwork','Mountain View, CA',
      'https://job-boards.greenhouse.io/gleanwork/jobs/4605446005',
      True,60,False,'mid','software_engineer',
      'Glean SWE with explicit security focus. AI+Security intersection — strong match for security + Python skills.',
      ['software engineer','security','AI','Python','backend','threat modeling'],
      ['Python','Linux','Docker','security engineering','backend systems'],
      ['prior combined SWE+security role']),
]

# ── REJECTS ────────────────────────────────────────────────────────────────────

# arizeai
results.append(j(19218,'AI Engineer, Instrumentation','arizeai','Remote (United States)',
    'https://job-boards.greenhouse.io/arizeai/jobs/5661972004',
    False,45,False,'mid','software_engineer',
    'ML observability/instrumentation role. Python relevant but requires ML platform experience.',
    ['ML observability','Python','OpenTelemetry','tracing'],['Python','Linux'],['ML platform experience','observability tooling']))

# attio
results.append(j(20268,'Product Engineer','attio','Remote',
    'https://jobs.ashbyhq.com/attio/70c55694-4f19-4077-b7fc-aa130048af62',
    False,42,False,'mid','software_engineer',
    'Attio product engineer. Generic SWE at CRM startup, likely mid-level.',
    ['product engineer','full stack','TypeScript','React'],['Python','backend development'],['TypeScript/React experience']))

# celonis
results.append(j(19602,'Associate Value Engineer (AI-Driven Data Science & Analytics) - Orbit Program','celonis','New York, US, New York',
    'https://job-boards.greenhouse.io/celonis/jobs/7627647003?gh_jid=7627647003',
    False,32,True,'entry_level','other',
    'Celonis Orbit Program is a management consulting/value engineering rotational — not a SWE/security role.',
    ['value engineer','data science','analytics','consulting'],['Python','data analysis'],['consulting background','business acumen']))

# cohere misc SWE
for rid, title, score, reasoning in [
    (17951,'Software Engineer, Collect',45,'Generic SWE at Cohere. No seniority signal but likely requires experience. Python relevant.'),
    (17954,'Software Engineer, Internal Infrastructure (North America)',50,'Infrastructure SWE at Cohere NA. Docker/Linux skills relevant but Cohere expects production infra experience.'),
    (17965,'Software Engineer, Search Applications',45,'Search SWE at Cohere. Interesting but likely requires search/ML experience.'),
    (17982,'Full-Stack Software Engineer, Inference',45,'Full-stack inference SWE at Cohere. Niche ML stack, likely requires experience.'),
    (17983,'Site Reliability Engineer, Inference Infrastructure',50,'SRE at Cohere inference. Relevant SRE/infra skills but likely requires production experience.')]:
    results.append(j(rid,title,'cohere','Remote',
        f'https://jobs.ashbyhq.com/cohere/x',False,score,False,'mid','software_engineer',reasoning,
        ['Python','Linux','Docker','distributed systems'],['Python','Linux','Docker'],['prior industry SWE experience']))

# contentful non-security
for rid, title, loc, jid, score, role in [
    (19341,'Analytics Engineer','Denver, Colorado, United States','7544101',40,'data_engineer'),
    (19347,'Data Engineer','Denver, Colorado, United States','7544099',42,'data_engineer'),
    (19348,'Data Scientist','Denver, Colorado, United States','7548713',35,'other'),
    (19356,'Platform Engineer','Denver, Colorado, United States','7544103',50,'software_engineer')]:
    results.append(j(rid,title,'contentful',loc,'https://job-boards.greenhouse.io/contentful/jobs/'+jid,
        False,score,False,'mid',role,'Mid-level data/platform role at Contentful. Limited security relevance.',
        ['Python','SQL','data pipelines'],['Python','SQL','PostgreSQL'],['data engineering experience']))

# deepgram
for rid, title, score, reasoning in [
    (18110,'Backend Software Engineer - Active Learning Team',48,'Backend SWE at Deepgram voice AI. Python skills relevant but likely requires ML/audio experience.'),
    (18111,'Software Engineer - Deepgram for Restaurants',45,'SWE at Deepgram. Niche voice AI product vertical.'),
    (18114,'Research Engineer, Machine Learning Systems',32,'Research Engineer requires ML research background, likely PhD-preferred.'),
    (18115,'Backend Engineer- Inference Services',48,'Backend infra SWE at Deepgram. Docker/Python relevant but inference-specific experience expected.'),
    (18122,'Site Reliability Engineer - AI & ML Infrastructure (Kubernetes, AWS & Terraform)',50,'SRE at Deepgram. Kubernetes/AWS experience gap. Docker/Linux partial match.'),
    (18123,'Backend Software Engineer - Engine Team (Voice Agent)',48,'Voice agent backend SWE. Niche domain.'),
    (18124,'Software Engineer, Voice Agents / AI - Deepgram for Restaurants',45,'Voice AI SWE, niche product.'),
    (18133,'ML Ops Infrastructure Engineer',48,'MLOps infra — Docker/Linux relevant but MLOps tooling experience expected.'),
    (18135,'Network Engineer, Real-Time Infrastructure',50,'Network engineer at Deepgram. TCP/IP, network fundamentals match but real-time audio infra is specialized.')]:
    results.append(j(rid,title,'deepgram','Remote','https://jobs.ashbyhq.com/deepgram/x',
        False,score,False,'mid','software_engineer',reasoning,
        ['Python','Linux','Docker','distributed systems'],['Python','Linux','Docker'],['audio/ML domain experience']))

# elevenlabs misc
for rid, title, score, reasoning in [
    (18068,'Full-Stack Growth Engineer',48,'Full-stack growth eng at ElevenLabs. Frontend-heavy, likely mid-level.'),
    (18069,'Full-Stack Engineer (Back-End Leaning)',50,'Backend-leaning full stack at ElevenLabs. Python/backend partially relevant.'),
    (18070,'Full-Stack Engineer (Front-End Leaning)',38,'Frontend-leaning — not my focus.'),
    (18072,'Full-Stack Engineer',48,'Generic full-stack at ElevenLabs. Mid-level expected.'),
    (18076,'Automations Engineer',48,'Automations/workflow engineer. Python skills relevant but automation-specific tooling expected.'),
    (18077,'Safety Engineer',45,'AI Safety Engineer — AI safety research focus, not security/SWE.')]:
    results.append(j(rid,title,'elevenlabs','Remote','https://jobs.ashbyhq.com/elevenlabs/x',
        False,score,False,'mid','software_engineer',reasoning,
        ['Python','TypeScript','backend'],['Python','backend'],['prior industry experience']))

# gleanwork misc
for rid, title, loc, jid, score, reasoning in [
    (19243,'Cloud Infrastructure Engineer','San Francisco Bay Area','4547218005',48,'Cloud infra at Glean. Docker/Linux/infra skills partially match but Glean expects production cloud experience.'),
    (19254,'Machine Learning Engineer, AI Assistant & Autonomous AI Agents','San Francisco Bay Area','4605215005',35,'MLE requires ML background. Not primary skillset.'),
    (19255,'Machine Learning Engineer, Infrastructure','San Francisco Bay Area','4501783005',38,'MLE infra — some Docker/infra overlap but ML focus expected.'),
    (19256,'Machine Learning Engineer, LLM Evals & Observability','San Francisco Bay Area','4669417005',35,'LLM evals — specialized ML role.'),
    (19257,'Machine Learning Engineer, Search Quality','San Francisco Bay Area','4006735005',35,'ML search quality — ML background required.'),
    (19276,'Software Engineer, Agentic Runtime','San Francisco Bay Area','4616929005',48,'Agentic SWE at Glean. Interesting but likely mid-level.'),
    (19278,'Software Engineer, Backend','San Francisco Bay Area','4581643005',45,'Generic backend SWE at Glean. Mid-level expected.'),
    (19280,'Software Engineer, Billing & Revenue Platform','San Francisco Bay Area','4675862005',40,'Billing platform SWE. Limited security relevance.'),
    (19281,'Software Engineer, Context Platform','Mountain View, CA','4638008005',42,'Context platform SWE at Glean.'),
    (19282,'Software Engineer, Data Foundations','San Francisco Bay Area','4637208005',42,'Data foundations SWE. Some data pipeline relevance.'),
    (19283,'Software Engineer, Developer Productivity','San Francisco Bay Area','4614706005',42,'Dev productivity SWE.'),
    (19284,'Software Engineer, Frontend','San Francisco Bay Area','4006733005',28,'Frontend SWE — not my focus.'),
    (19285,'Software Engineer, Fullstack','San Francisco Bay Area','4006734005',42,'Generic fullstack at Glean.'),
    (19286,'Software Engineer, Insights','San Francisco, CA','4659229005',40,'Insights/analytics SWE.'),
    (19288,'Software Engineer, Platform','San Francisco Bay Area','4636739005',45,'Platform SWE at Glean.'),
    (19289,'Software Engineer, Product Backend','San Francisco Bay Area','4428090005',45,'Product backend SWE at Glean.')]:
    results.append(j(rid,title,'gleanwork',loc,'https://job-boards.greenhouse.io/gleanwork/jobs/'+jid,
        False,score,False,'mid','software_engineer',reasoning,
        ['Python','backend','distributed systems'],['Python','Linux','Docker'],['prior SWE experience','Glean stack']))

# helsing misc
results.append(j(19835,'Software Engineer - Infrastructure','helsing','Washington, DC',
    'https://helsing.ai/jobs/4729613101?gh_jid=4729613101',
    False,52,False,'mid','software_engineer',
    'Helsing infra SWE, DC. Docker/Linux/infra skills relevant but defense company expects production infra experience.',
    ['infrastructure','Python','Linux','Docker','Kubernetes'],['Python','Linux','Docker'],['Kubernetes production ops','defense sector experience']))

# hightouch
for rid, title, jid, score in [
    (19316,'Developer Productivity Engineer','5701750004',45),
    (19321,'Full Stack Product Engineer','4620430004',45),
    (19329,'Software Engineer, AI Agents','5542602004',48),
    (19330,'Software Engineer - AI Productivity','5809895004',48),
    (19331,'Software Engineer, Control Plane','5426891004',48),
    (19332,'Software Engineer, Customer Studio Backend','4782625004',45),
    (19333,'Software Engineer, Distributed Systems','4782632004',50),
    (19334,'Software Engineer, Journeys','5698845004',45),
    (19335,'Software Engineer, Streaming Systems','5731011004',50),
    (19340,'Web Engineer','5734303004',30)]:
    results.append(j(rid,title,'hightouch','Remote (North America)',
        'https://job-boards.greenhouse.io/hightouch/jobs/'+jid,
        False,score,False,'mid','software_engineer',
        'Hightouch data activation SWE. Mid-level expected. Some distributed systems relevance.',
        ['Python','TypeScript','distributed systems','data pipelines'],['Python','Linux'],['prior industry SWE role']))

# inngest
results.append(j(20332,'Distributed Systems Engineer - Platform','inngest','Remote',
    'https://jobs.ashbyhq.com/inngest/ae72d036-b98b-4abb-8454-a687870cf0ca',
    False,50,False,'mid','software_engineer',
    'Distributed systems engineer at Inngest. Relevant background in distributed/event systems but likely requires experience.',
    ['distributed systems','Go','TypeScript','event-driven'],['Python','Linux','Kafka','Docker'],['Go experience','production distributed systems']))

# langchain
for rid, title, loc in [
    (18011,'Python OSS Engineer',''),
    (18019,'FullStack Engineer, Observability & Evals Platform (LangSmith)',''),
    (18023,'Developer Productivity',''),
    (18032,'Deployed Engineer (San Francisco)',''),
    (18033,'Deployed Engineer (NYC)',''),
    (18034,'Deployed Engineer (Austin)','Remote'),
    (18042,'Deployed Engineer (Dallas)','Remote'),
    (18046,'Deployed Engineer (Boston)',''),
    (18048,'Deployed Engineer (Atlanta)',''),
    (18052,'Deployed Engineer (Chicago)','Remote'),
    (18053,'Deployed Engineer (San Diego)',''),
    (18054,'Deployed Engineer (Los Angeles)',''),
    (18055,'Deployed Engineer (Charlotte)','Remote'),
    (18056,'Deployed Engineer (Raleigh)','Remote'),
    (18057,'Deployed Engineer (Seattle)','Remote')]:
    is_deployed = 'Deployed' in title
    score = 38 if is_deployed else 48
    reasoning = ('LangChain Deployed Engineer is a customer-facing field/solutions engineering role, not core SWE. Requires enterprise customer engagement.'
                 if is_deployed else 'LangChain SWE/eng role. Python very relevant but LangChain expects framework expertise.')
    results.append(j(rid,title,'langchain',loc,'https://jobs.ashbyhq.com/langchain/x',
        False,score,False,'mid','software_engineer',reasoning,
        ['Python','LangChain','LangGraph','RAG'],['Python','backend development'],
        ['LangChain framework expertise','customer-facing experience' if is_deployed else 'OSS contributions']))

# lindy data eng
results.append(j(20264,'Data Engineer','lindy','',
    'https://jobs.ashbyhq.com/lindy/e56a424d-5a40-450b-8978-cd5e7c86deed',
    False,40,False,'mid','data_engineer',
    'Lindy data engineer. Data pipelines overlap with Kafka/PyFlink background but data eng focus not primary target.',
    ['data engineering','Python','SQL','ETL'],['Python','PostgreSQL','Kafka'],['data engineering experience']))

# lovable misc
for rid, title, score, reasoning in [
    (20334,'Data Platform Engineer',48,'Lovable data platform. Python/data pipelines some relevance.'),
    (20335,'Engineer - Agents & Evals',50,'Agents + evals engineer at Lovable. Interesting but niche AI product.'),
    (20336,'Backend Product Engineer',50,'Backend product SWE at Lovable. Python/backend relevant.'),
    (20337,'Fullstack Product Engineer',48,'Fullstack product at Lovable. Mid-level expected.'),
    (20342,'Fullstack Engineer - AI Code Security',55,'AI code security SWE. Security angle relevant but Lovable is Swedish startup, entry-level unclear.'),
    (20345,'Platform Engineer - Developer Experience',48,'Platform/devex SWE at Lovable.'),
    (20346,'Software Engineer - Infrastructure',50,'Infra SWE at Lovable. Docker/Linux skills partially relevant.'),
    (20349,'Fullstack Growth Engineer',45,'Growth engineering at Lovable. Not security-focused.'),
    (20361,'GRC Engineer',50,'Lovable GRC Engineer. NIST/ISO 27001 background relevant for governance/compliance but specialized role.'),
    (20366,'Fullstack Growth Engineer',45,'Duplicate growth eng role.')]:
    results.append(j(rid,title,'lovable','','https://jobs.ashbyhq.com/lovable/x',
        False,score,False,'mid','software_engineer',reasoning,
        ['Python','TypeScript','security'],['Python','Linux','Docker'],['prior industry role']))

# mistral
results.append(j(20193,'Software Engineer, Cloud Deployments','mistral','New York, NY',
    'https://jobs.lever.co/mistral/4db39406-fcec-4f12-abc1-42ecaa50d84f',
    False,50,False,'mid','software_engineer',
    'Mistral cloud deployments SWE, NY. Infrastructure/cloud focus, Docker/Linux relevant but likely requires cloud deployment experience.',
    ['cloud deployments','Python','Kubernetes','AWS','Docker'],['Python','Linux','Docker'],['cloud deployment experience','Kubernetes production']))

# palantir non-new-grad
for rid, title, loc, slug, score, reasoning in [
    (19953,'Application Security Engineer','New York, NY','7e3ec54c-b73a-4014-8ef3-cdce8a4953c4',52,'Palantir AppSec. Great title but non-new-grad Palantir roles require 2-5y experience.'),
    (19954,'Application Security Engineer','Palo Alto, CA','86641a6e-5abb-40c5-8cc3-d481f70350d7',52,'Palantir AppSec Palo Alto. Same as NY — requires experience.'),
    (19955,'Application Security Engineer','Washington, D.C.','a5fdd5ec-d1f3-4837-83af-161b003931dd',52,'Palantir AppSec DC. Likely requires clearance and experience.'),
    (19956,'Application Security Engineer','Remote: United States','ce813413-de04-4a7b-a796-43735f55bf0c',52,'Palantir AppSec Remote US. Best location option but still mid-level expectations.'),
    (19957,'Application Security Engineer','Seattle, WA','f8df815c-6a38-4d57-b75f-c4262b9311b4',52,'Palantir AppSec Seattle.'),
    (19960,'Backend Software Engineer - Application Development','New York, NY','ab7e3425-81d5-4705-a7b5-cd60c8a45cdb',48,'Palantir backend SWE. Mid-level expected.'),
    (19961,'Backend Software Engineer - Defense','Washington, D.C.','1345438c-ebfc-4fa5-b545-30c1414f317c',48,'Palantir defense backend. Clearance likely required.'),
    (19962,'Backend Software Engineer - Defense','Palo Alto, CA','a8174f9c-6f46-46b4-8e15-d1ff9e37c9eb',48,'Palantir defense backend Palo Alto.'),
    (19963,'Backend Software Engineer - Defense','New York, NY','d33e0c31-ac7e-4f57-ba74-36f2df6ae2f5',48,'Palantir defense backend NY.'),
    (19964,'Backend Software Engineer - Infrastructure','New York, NY','6fe5515f-f677-4d98-8ac2-1775a425f5e7',50,'Palantir infra SWE. Docker/Linux relevant but mid-level.'),
    (19966,'Backend Software Engineer - Infrastructure, Foundations','New York, NY','fb2d3222-dbd8-4e03-8d39-47b820e9509c',50,'Palantir infra foundations SWE.'),
    (19967,'Compliance Engineer','New York, NY','6fa1ad9b-4506-45e4-a476-f4292911a279',48,'Palantir compliance eng. NIST/ISO background partially relevant but mid-level.'),
    (19968,'Compliance Engineer','Palo Alto, CA','755c16c2-5207-49a7-9e7d-55eb608e03e6',48,'Palantir compliance eng Palo Alto.'),
    (19969,'Compliance Engineer','Washington, D.C.','fbf8b12b-38f3-4cdb-a4d3-b5404c0aa98a',48,'Palantir compliance eng DC.'),
    (20023,'Full Stack Software Engineer - Application Development','New York, NY','2da4be12-bc7a-4950-87db-e9d68d955ff7',48,'Palantir full stack SWE. Mid-level.'),
    (20026,'Incident Management Engineer','New York, NY','b72abc17-293d-47e0-a094-c1ab0016b794',50,'Palantir incident management. Ops/SRE flavored, relevant but mid-level.'),
    (20027,'Industrial Security Specialist','New York, NY','12d13a31-5764-4678-8835-809f0deae49b',40,'Palantir industrial security. Physical security/clearance focus, not cyber.'),
    (20028,'Industrial Security Specialist','Washington, D.C.','320bc538-d707-4976-9ad1-44568c0a8ab9',40,'Palantir industrial security DC. Clearance required.'),
    (20029,'Information Security Engineer','Seattle, WA','1124402c-2088-40c6-b6aa-b9ef7777519b',55,'Palantir InfoSec Eng Seattle. Good title but non-new-grad Palantir expects 2-3y.'),
    (20030,'Information Security Engineer','Washington, D.C.','36703f67-6fae-445c-9277-f946121faaa0',55,'Palantir InfoSec Eng DC. Clearance likely needed.'),
    (20031,'Information Security Engineer','New York, NY','e2a8360a-710a-4185-b2a9-3b7d9fe590b1',55,'Palantir InfoSec Eng NY. Best location. Still mid-level expectations.'),
    (20032,'Information Systems Security Engineer','Washington, D.C.','caeb42e8-5d44-4114-a912-0de2584d1a75',42,'ISSE at Palantir DC. Clearance almost certainly required.'),
    (20037,'Platform Intelligence Engineer','New York, NY','a753a9e7-a361-426b-9c25-3cf2488c1730',45,'Platform intelligence SWE at Palantir. Mid-level.'),
    (20041,'Product Infrastructure Security Engineer','Remote: US - East','0f077970-31ad-45b4-ae76-458a134b705f',55,'Palantir Product Infra Security, Remote US East. Excellent title but mid-level.'),
    (20042,'Product Infrastructure Security Engineer','Washington, D.C.','15f01f3a-922d-4cff-b093-888333d88628',55,'Palantir Product Infra Security DC.'),
    (20043,'Product Infrastructure Security Engineer','Palo Alto, CA','346ff0e0-94dd-4d6c-916a-23ecdd74bbc6',55,'Palantir Product Infra Security Palo Alto.'),
    (20044,'Product Infrastructure Security Engineer','Seattle, WA','47bf61f0-853c-43f9-ad30-873784da9c59',55,'Palantir Product Infra Security Seattle.'),
    (20045,'Product Infrastructure Security Engineer','New York, NY','d617af53-e943-4122-8993-4f5853c667bf',55,'Palantir Product Infra Security NY.'),
    (20046,'Product Reliability Engineer - Defense','New York, NY','250f623c-9afb-4c91-b0c0-25d4e83005ec',45,'Palantir defense reliability eng. Mid-level, defense focus.'),
    (20047,'Product Reliability Engineer - Defense','Washington, D.C.','57699414-b373-4a5e-9be8-6fb7de41ea72',45,'Palantir defense reliability eng DC.'),
    (20065,'Site Reliability Engineer - US Government','Washington, D.C.','211f99dc-269e-4f25-84d3-d73dea782080',48,'Palantir SRE US Gov, DC. SRE skills partially relevant but clearance and production SRE experience expected.'),
    (20070,'Software Engineer - Apollo Platform','New York, NY','8f308f3e-43d2-49c9-accd-cc7af0f1565c',48,'Palantir Apollo Platform SWE.'),
    (20071,'Software Engineer - Apollo Platform','Seattle, WA','afea07a8-2721-45e6-a9ca-6580f3f9783c',48,'Palantir Apollo Platform SWE Seattle.'),
    (20073,'Software Engineer - Apollo Systems','New York, NY','832e4652-5088-4e5b-aeac-1e82ec3ebad4',48,'Palantir Apollo Systems SWE.'),
    (20074,'Software Engineer - Apollo Systems','Seattle, WA','e47d4410-2542-47d8-b558-b5295fc28821',48,'Palantir Apollo Systems SWE Seattle.'),
    (20075,'Software Engineer - Core Interfaces','Palo Alto, CA','cf76738e-3030-42fa-92ac-a9446df956fc',45,'Palantir core interfaces SWE.'),
    (20076,'Software Engineer - Defense Applications','Washington, D.C.','f7dbfdf1-0bb1-4c11-ac15-6a139cee3410',45,'Palantir defense apps SWE. Clearance likely required.'),
    (20077,'Software Engineer - Developer Productivity','New York, NY','3c84af24-b7aa-483e-b2c3-e1d83494fe15',48,'Palantir dev productivity SWE.'),
    (20078,'Software Engineer - Edge','Washington, D.C.','397fb983-47b7-4a53-a7df-f080f43f7720',48,'Palantir edge SWE. Interesting distributed/edge work.'),
    (20079,'Software Engineer - Environment Platform','Seattle, WA','cd2423c6-da68-430c-8be5-0ae7eea36497',48,'Palantir environment platform SWE.'),
    (20080,'Software Engineer - Environment Platform','New York, NY','d5d83a8f-cb96-41cc-9612-c7224fbb2fbc',48,'Palantir environment platform SWE NY.'),
    (20081,'Software Engineer - Frontend Developer Productivity','New York, NY','71ed917e-850a-484b-9454-fa66bdf24540',32,'Palantir frontend dev productivity. Frontend focus, not my strength.'),
    (20110,'Systems Engineer - Business Systems','New York, NY','78dbb616-cf3c-489c-9eb2-e6fc9bd9993a',32,'Palantir business systems engineer — IT systems admin role, not SWE/security.'),
    (20111,'Systems Engineer - Business Systems','Washington, D.C.','da426d8b-5963-42e5-9b19-84649cb519cc',32,'Same role as NY.'),
    (20112,'Systems Engineer - Business Systems','Denver, CO','df20ad9f-3d7f-4267-8e37-8253f717534a',32,'Same role, Denver.'),
    (20113,'Systems Engineer - Business Systems','Palo Alto, CA','e1d6117e-2ee0-4cf6-8040-256c3009389f',32,'Same role, Palo Alto.'),
    (20114,'Systems Engineer - Microsoft 365','Washington, D.C.','4fbe610c-a1f2-47ca-9932-4bc35e65ee31',28,'M365 admin role. IT sysadmin, not SWE.'),
    (20115,'Systems Engineer - Microsoft 365','New York, NY','810e07f1-0f24-432e-a615-58478bf6ee51',28,'M365 admin NY.'),
    (20122,'Web Application Developer - Defense','Washington, D.C.','4255e21c-d0f2-4f57-b5db-1f65830d6425',45,'Palantir web app dev defense, DC. Web dev + defense context.'),
    (20123,'Web Application Developer - Defense','New York, NY','6a82fd06-5754-46c2-8214-9ca4cd89fb9d',45,'Palantir web app dev defense NY.'),
    (20124,'Web Application Developer - Defense','Palo Alto, CA','96e4295f-3af7-48e5-a2c8-74622eaf5587',45,'Palantir web app dev defense Palo Alto.')]:
    results.append(j(rid,title,'palantir',loc,'https://jobs.lever.co/palantir/'+slug,
        False,score,False,'mid','software_engineer' if 'Security' not in title and 'ISSE' not in title else 'security_engineer',
        reasoning,['Python','Linux','Docker','backend'],['Python','Linux','Docker'],['prior Palantir-level experience']))

# parloa
results.append(j(19109,'Partner Solution Engineer','parloa','Remotely in the USA',
    'https://job-boards.eu.greenhouse.io/parloa/jobs/4780830101',
    False,32,False,'mid','other',
    'Sales/solutions engineering role. Customer-facing, enterprise demos. Not core SWE/security.',
    ['solutions engineering','enterprise sales','Python','APIs'],['Python','API integration'],['sales engineering experience','customer-facing role']))

# pinecone
results.append(j(18066,'Associate Field Engineer','pinecone','Remote',
    'https://jobs.ashbyhq.com/pinecone/3d2a4732-6460-479f-b16b-12112c48ca5f',
    False,35,False,'entry_level','other',
    'Pinecone Associate Field Engineer — customer success/solutions role, not core SWE. Associate signal but wrong role family.',
    ['field engineer','vector database','Python','customer success'],['Python'],['customer-facing experience','Pinecone/vector DB expertise']))

# plaid misc
for rid, title, loc, slug, score, reasoning in [
    (19905,'Data Scientist - Network Value','San Francisco','18503c02-17a0-4c47-98c8-155b0b6ccc2a',32,'Data scientist at Plaid. Not my target role.'),
    (19912,'Executive Assistant, Product & Engineering','New York','8bc2bf33-95a0-4783-a21f-bd73a1a61149',10,'Admin/EA role. Not relevant.'),
    (19916,'New Business Associate - Inbound','San Francisco','177857f0-5455-4af7-ae04-1bedb3a1bc27',15,'Sales/BD role. Not relevant.'),
    (19940,'Software Engineer','New York','49139a62-a9bc-4400-ae89-789818b34cb8',52,'Plaid SWE NY. Fintech backend, relevant skills but mid-level expected.'),
    (19941,'Software Engineer','Seattle, WA','f455a60a-6ea0-4d1b-890b-5f7869192c5f',52,'Plaid SWE Seattle.'),
    (19942,'Software Engineer','San Francisco','f456f4fa-a9f7-4673-892a-8943e3cfa3fe',52,'Plaid SWE SF.'),
    (19943,'Software Engineer - Platform','San Francisco','2b9a141e-0669-4197-aa52-2b07d9fadc96',52,'Plaid Platform SWE SF.')]:
    results.append(j(rid,title,'plaid',loc,'https://jobs.lever.co/plaid/'+slug,
        False,score,False,'mid','software_engineer' if score > 20 else 'other',reasoning,
        ['Python','backend','fintech'],['Python','backend','PostgreSQL'],['fintech domain experience']))

# planetscale
results.append(j(19431,'Software Engineer - Infrastructure','planetscale','San Francisco Bay Area or Remote',
    'https://job-boards.greenhouse.io/planetscale/jobs/4036240009',
    False,50,False,'mid','software_engineer',
    'PlanetScale infra SWE. MySQL/distributed DB infra — interesting but requires production database/infra experience.',
    ['infrastructure','MySQL','distributed systems','Kubernetes','Go'],['Linux','Docker','distributed systems basics'],['MySQL/DB internals','production infra experience']))

# resend
for rid, title, score, reasoning in [
    (20327,'Open Source Engineer',45,'Resend OSS engineer. Python/developer tooling somewhat relevant but OSS contributions expected.'),
    (20329,'Developer Experience Engineer',35,'DevEx/DevRel hybrid at Resend. Not core SWE/security.')]:
    results.append(j(rid,title,'resend','Remote','https://jobs.ashbyhq.com/resend/x',
        False,score,False,'mid','software_engineer',reasoning,
        ['Python','OSS','developer tools'],['Python','GitHub'],['OSS track record']))

# runpod misc
results.append(j(19237,'Software Engineer (Full-Stack)','runpod','Remote, USA',
    'https://job-boards.greenhouse.io/runpod/jobs/4785681008',
    False,52,False,'mid','software_engineer',
    'RunPod full-stack SWE, Remote US. GPU cloud company, Python/backend relevant but full-stack scope broad.',
    ['full stack','Python','backend','React','Docker'],['Python','Linux','Docker','backend'],['full-stack frontend experience']))

# spotify US
for rid, title, slug, score, reasoning in [
    (17796,'Backend Engineer - Data Infrastructure','66492688-d5b0-4cf8-b1a4-4a715157edd9',45,'Spotify data infra backend. Python/Kafka relevant but mid-level at Spotify.'),
    (17797,'Backend Engineer - Advertising','1689082c-9265-431f-9e55-ef7666e41283',40,'Spotify ads backend. Mid-level, advertising domain.'),
    (17801,'Backend Engineer - Platform Developer Experience','31bf7d45-9448-413c-8f61-b69a8f636f82',45,'Spotify platform devex. Mid-level.'),
    (17805,'Backend Engineer, Music','52fe2b49-3c85-4479-b1db-2c5ab74cbcfc',40,'Spotify music backend. Python/backend relevant but mid-level, music domain.'),
    (17806,'Backend Engineer, Music','ee5064af-0116-4ef2-994a-cb8fed580290',40,'Same as above.'),
    (17807,'Backend Engineer, Podcast','454e6013-78ca-4009-9ad4-7597f2045d0a',40,'Spotify podcast backend.'),
    (17834,'Fullstack Engineer - Platform Developer Experience','651491f7-cd91-49bd-93f5-eb939344463b',42,'Spotify fullstack, platform devex.'),
    (17837,'Machine Learning Engineer','e200d025-4cff-4eb8-afa4-6680e31c43a2',32,'MLE at Spotify. ML background required.'),
    (17838,'Machine Learning Engineer','e68ad741-4c4e-4b06-ae11-9cf1e36dd40f',32,'MLE at Spotify duplicate.'),
    (17839,'Machine Learning Engineer, Personalization','de3f6a47-4d75-4512-8351-b362f1d1c32e',32,'ML personalization at Spotify.'),
    (17889,'Site Reliability Engineer - Backstage','ad5ef898-b800-4213-a63e-e39a97df9cfb',48,'SRE at Spotify. Backstage OSS. Docker/Linux relevant but mid-level SRE expected.')]:
    results.append(j(rid,title,'spotify','New York, NY','https://jobs.lever.co/spotify/'+slug,
        False,score,False,'mid','software_engineer',reasoning,
        ['Python','backend','Kafka','distributed systems'],['Python','Linux','Docker','Kafka'],['prior Spotify-level SWE experience']))

# stabilityai
results.append(j(19307,'Generative AI Inference Engineer','stabilityai','United States',
    'http://stability.ai/careers?gh_jid=4712826101',
    False,35,False,'mid','software_engineer',
    'StabilityAI generative AI inference. Very specialized ML/inference role requiring deep ML knowledge.',
    ['generative AI','inference','CUDA','PyTorch','Python'],['Python'],['ML research background','CUDA/GPU programming']))

# supabase
for rid, title, score, reasoning in [
    (20303,'Developer Relations Engineer (San Francisco, CA)',32,'DevRel role. Not SWE/security.'),
    (20311,'Software Engineer - Support Tooling (APAC/AMER)',48,'Supabase support tooling SWE. APAC/AMER scope, some backend relevance.'),
    (20312,'GTM Engineer',28,'GTM/sales engineering. Not relevant.'),
    (20313,'Customer Reliability Engineer',45,'Customer-facing SRE at Supabase. Some reliability/SRE relevance.'),
    (20314,'Platform Engineer: Data',48,'Data platform engineer at Supabase. PostgreSQL/infra skills partially relevant.'),
    (20322,'Software Engineer - Supavisor',50,'Supabase connection pooler SWE. PostgreSQL experience relevant.'),
    (20323,'Product Engineer - Auth',52,'Auth SWE at Supabase. Authentication/security overlap with profile.'),
    (20324,'Foundation Engineer (Golang) - Auth',48,'Go auth engineer at Supabase. Auth/security relevant but Go experience gap.')]:
    results.append(j(rid,title,'supabase','Remote','https://jobs.ashbyhq.com/supabase/x',
        False,score,False,'mid','software_engineer',reasoning,
        ['PostgreSQL','Go','Python','backend'],['Python','PostgreSQL','backend'],['Go experience','OSS database experience']))

# synthesia
results.append(j(20381,'Software Engineer, Machine Learning','synthesia','Remote',
    'https://jobs.ashbyhq.com/synthesia/b1f960fd-f07a-4788-8e5c-8a7c62c77fb2',
    False,35,False,'mid','software_engineer',
    'Synthesia ML SWE. ML/deep learning focus for video synthesis. Requires ML background.',
    ['machine learning','Python','PyTorch','deep learning'],['Python'],['ML/deep learning experience']))

# vapi
results.append(j(18141,'Agent Engineer','vapi','Remote',
    'https://jobs.ashbyhq.com/vapi/a69077ea-c968-42ae-bb74-bd782c790211',
    False,48,False,'mid','software_engineer',
    'Vapi agent engineer. Voice AI agents, Python relevant but niche voice AI domain expected.',
    ['agents','Python','voice AI','APIs'],['Python','backend','Docker'],['voice AI/telephony experience']))

# wayve
for rid, title, loc, jid, score, reasoning in [
    (19722,'Application Software Engineer - Software Integration / Embedded Software','Sunnyvale','8478666002',42,'Wayve autonomous driving SWE. Embedded/integration focus, likely requires automotive/embedded experience.'),
    (19723,'Application Software Engineer - Software Integration / Embedded Software','Detroit','8449034002',42,'Same role, Detroit.'),
    (19725,'Cloud Infrastructure Engineer','Sunnyvale','8483723002',48,'Wayve cloud infra. Docker/Linux/cloud relevant but AV-specific infra expected.'),
    (19727,'Customer Integration Engineer','Sunnyvale','8500131002',35,'Customer-facing integration role. Not core SWE.'),
    (19728,'Customer Integration Engineer','Detroit','8501381002',35,'Same, Detroit.'),
    (19737,'Machine Learning Engineer, App SW','Sunnyvale','8435254002',35,'Wayve MLE. ML background required for AV ML.'),
    (19761,'Software Engineer - OS & Kernel, Robot Software','Sunnyvale','8423176002',50,'Wayve OS/Kernel SWE. Linux kernel work interesting given Linux background but AV-specific robotics/embedded experience expected.'),
    (19762,'Software Engineer - Sensor Systems, Robot Software','Sunnyvale','8423839002',38,'Sensor systems SWE. Hardware/sensor domain — specialized.'),
    (19763,'Software Engineer - System Performance, Robot Software','Sunnyvale','8482117002',45,'System performance SWE. Performance tuning/optimization relevant but AV context.')]:
    results.append(j(rid,title,'wayve',loc,'https://wayve.firststage.co/jobs?gh_jid='+jid,
        False,score,False,'mid','software_engineer',reasoning,
        ['Python','Linux','C++','embedded systems'],['Python','Linux'],['automotive/robotics experience','C++ proficiency']))

print(f'Total records: {len(results)}')
print(f'Keeps: {sum(1 for r in results if r["keep_in_db"])}')
print(f'Rejects: {sum(1 for r in results if not r["keep_in_db"])}')

with open('/app/scripts/batch4_results.json','w') as f:
    json.dump(results, f, indent=2)
print('Written /app/scripts/batch4_results.json')
