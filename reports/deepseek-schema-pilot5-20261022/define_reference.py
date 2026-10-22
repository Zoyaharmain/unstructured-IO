"""Freeze analyst-defined critical field opportunities BEFORE provider mapping."""
import json,re,unicodedata
from pathlib import Path
OUT=Path(__file__).parent
facts=[]
def norm(s):return ' '.join(unicodedata.normalize('NFKC',str(s)).casefold().split())
def fact(doc,collection,selector,field,value,sources,reason='Explicit source fact'):
 blocks=json.loads((OUT/f'{doc:02d}/source-blocks.json').read_text());byid={b['source_id']:b for b in blocks}
 for source in sources:assert source in byid,source
 facts.append({'id':f'f{len(facts)+1:03d}','document':doc,'collection':collection,'selector':selector,
  'field':field,'expected':value,'source_ids':sources,'reason':reason})
def root(doc,path,value,source):fact(doc,'root',None,path,value,[source])
def job(doc,company,role,start,end,sources):
 fact(doc,'experience',{'company':company},'company',company,[sources[0]])
 if role:fact(doc,'experience',{'company':company},'role',role,[sources[1]])
 if start:fact(doc,'experience',{'company':company},'start_date',start,[sources[2]])
 if end:fact(doc,'experience',{'company':company},'end_date',end,[sources[2]])
def edu(doc,degree,institution,source,year=None,date_source=None,grade=None):
 fact(doc,'education',{'degree':degree},'degree',degree,[source])
 if institution:fact(doc,'education',{'degree':degree},'institution',institution,[source] if isinstance(institution,str) else institution)
 if year:fact(doc,'education',{'degree':degree},'graduation_year',year,[date_source])
 if grade:fact(doc,'education',{'degree':degree},'grade_or_gpa',grade,[date_source])
# 1: one-page finance.
root(1,'contact.full_name','Ajay Bandagi','e0:0:13');root(1,'contact.email','ajaybandagi1998@gmail.com','e1:0:25');root(1,'contact.phone','+91 9604657161','e2:0:14')
root(1,'professional_title','Senior Accounts Executive','e0:13:125');root(1,'total_experience_years',3.5,'e0:13:125')
job(1,'Vigocare Private Limited','Senior Accounts Executive – Finance Operations & Statutory Compliance','Dec 2023','Present',['e6:0:36','e7:0:69','e8:0:18'])
job(1,'Godavari Cuts',None,'Feb 2023','Dec 2023',['e10:0:25','e10:0:25','e9:1360:1379'])
fact(1,'education',{'degree':'Master of Business Administration (MBA) – Finance'},'degree','Master of Business Administration (MBA) – Finance',['e16:0:49'])
fact(1,'education',{'degree':'Master of Business Administration (MBA) – Finance'},'institution','Yashwantrao Chavan Maharashtra Open University',['e15:0:46'])
fact(1,'education',{'degree':'Master of Business Administration (MBA) – Finance'},'start_year','2024',['e17:0:53'])
fact(1,'education',{'degree':'Master of Business Administration (MBA) – Finance'},'graduation_year','2026',['e17:0:53'],'Expected completion explicitly marked; must not imply an already earned degree')
fact(1,'education',{'degree':'Bachelor of Commerce (B.Com) – Finance & Accounts'},'degree','Bachelor of Commerce (B.Com) – Finance & Accounts',['e18:2:51'])
fact(1,'education',{'degree':'Bachelor of Commerce (B.Com) – Finance & Accounts'},'start_year','2021',['e19:0:21'])
fact(1,'education',{'degree':'Bachelor of Commerce (B.Com) – Finance & Accounts'},'graduation_year','2024',['e19:0:21'])
# 2: programming languages must not become spoken languages.
root(2,'contact.full_name','D Dhanush','e0:0:9');root(2,'contact.email','dhanushdevaraj17@gmail.com','e1:0:60');root(2,'contact.phone','9380249870','e1:0:60')
root(2,'contact.linkedin_url','https://www.linkedin.com/in/d-dhanush-a733521b3/','e1:60:157');root(2,'contact.github_url','https://github.com/ddhanushd','e1:60:157')
job(2,'CitiusTech Health Technologies Pvt. Ltd.','Software Engineer','July 2022','September 2023',['e6:16:87','e6:16:87','e7:0:26'])
job(2,'Independent Projects','Freelance Java Developer','October 2023','Present',['e11:0:47','e11:0:47','e12:0:22'])
for degree,institution,source,inst,dates,year,grade in [
 ('B.E. in Electronics and Communication Engineering','M S Ramaiah Institute of Technology','e26:10:60','e26:60:95','e27:0:24','2022','7.85/10'),
 ('Intermediate (PUC) – Science','Sarvodaya PU College','e28:0:29','e28:29:49','e29:0:21','2018','89.83%')]:
 fact(2,'education',{'degree':degree},'degree',degree,[source]);fact(2,'education',{'degree':degree},'institution',institution,[inst]);fact(2,'education',{'degree':degree},'graduation_year',year,[dates]);fact(2,'education',{'degree':degree},'grade_or_gpa',grade,['e27:24:37' if year=='2022' else 'e29:21:39'])
for name,source in [('Healthcare Patient Management System','e16:13:52'),('Hotel Rating Microservices Application','e20:0:41'),('Stock Market Investing Application','e24:0:37')]:fact(2,'projects',{'name':name},'name',name,[source])
fact(2,'certifications',{'name':'Java (Basic)'},'issuer','HackerRank',['e32:74:101'])
# 3: dense compact backend resume.
root(3,'contact.full_name','BOOVANESH KUMAR','e0:0:16');root(3,'contact.email','boovaneshbk123@gmail.com','e0:112:213');root(3,'contact.phone','7708126940','e0:112:213');root(3,'total_experience_years',3,'e1:21:155')
job(3,'Mitrahsoft','Software Engineer',None,None,['e2:0:30','e2:0:30','e2:0:30'])
for degree,institution,source in [('Bachelor of Engineering','Kongu Engineering College','e22:10:76'),('HSC',"St. Paul's Matriculation Hr. Sec. School",'e22:76:123'),('SSLC',"St. Paul's Matriculation Hr. Sec. School",'e22:123:170')]:
 fact(3,'education',{'degree':degree},'degree',degree,[source]);fact(3,'education',{'degree':degree},'institution',institution,[source])
for name,source in [('Ecommerce Application','e8:0:21'),('HRMS — Human Resource Management System','e15:0:39'),('Freight Management System — Microservices','e20:0:41')]:fact(3,'projects',{'name':name},'name',name,[source])
for name,source in [('AWS Certified Solutions Architect – Associate','e24:2:55'),('Cyber Security From Beginner to Expert','e24:58:104'),('Software Architecture and Design of Modern Large Scale Systems','e24:107:177')]:fact(3,'certifications',{'name':name},'issuer','Udemy',[source])
# 4: explicitly labeled employers/roles/clients.
root(4,'contact.full_name','A MADHAVI','e0:0:9');root(4,'contact.email','madhavi.aradhyula03@gmail.com','e1:0:29');root(4,'contact.phone','+91-9494916311','e2:0:14');root(4,'professional_title','Business Analyst','e4:0:22');root(4,'total_experience_years',8,'e5:21:139')
for company,role,start,end,line,date in [
 ('Tech Mahindra','Business Analyst cum UAT Tester','Aug 2022','Present','e24:0:58','e24:58:153'),
 ('Pine Labs','Sr QA Cum Product Owner','Jan 2022','June 2022','e37:0:46','e37:46:149'),
 ('Capgemini','Consultant','May 2021','Dec 2021','e45:0:33','e45:33:135'),
 ('National Payments Corporation of India','Senior Associate','Jan 2017','May 2021','e52:0:68','e52:68:119')]:
 job(4,company,role,start,end,[line,line,date]);fact(4,'experience',{'company':company},'location','Hyderabad',[date])
fact(4,'education',{'degree':'Bachelor of Engineering in ECE'},'degree','Bachelor of Engineering in ECE',['e80:10:113']);fact(4,'education',{'degree':'Bachelor of Engineering in ECE'},'graduation_year','2015',['e80:10:113'])
for name,year,source in [('Certified Scrum Product Owner (CSPO)','2025','e77:17:59'),('Fundamentals of SWIFT MT & ISO20022','2020','e78:0:49'),('Trained in Embedded Systems','2016','e79:0:48')]:fact(4,'certifications',{'name':name},'issue_year',year,[source])
# 5: research CV. Education dates are deliberately excluded: detached columns.
root(5,'contact.full_name','NITHIN ESWARAPPA','e0:0:16');root(5,'contact.phone','9916476627','e1:0:30');root(5,'total_experience_years',7,'e6:402:413')
for company,role,start,end,line,date in [
 ('GITAM University','RESEARCH ASSOCIATE','Oct 2023','Now','e28:0:80','e29:0:14'),
 ('Vimaan.ai','Senior Firmware Engineer - Robotics','Apr 2020','Jul 2022','e48:0:46','e49:0:21'),
 ('Tonbo Imaging','Member of Technical Staff','Apr 2015','Jun 2018','e53:0:40','e54:0:21'),
 ('Siemens Information Systems Ltd.','Systems Engineer','Jul 2008','Apr 2009','e67:0:50','e66:98:201')]:
 if company=='Siemens Information Systems Ltd.':
  # Its dates occur in the next span, before the employer; keep the association ambiguous.
  start=end=None
 job(5,company,role,start,end,[line,line,date])
for degree,source in [('Master Of Technology In Intelligent Systems','e8:38:82'),('Bachelor of Engineering in Electronics and Communication','e8:120:176')]:
 fact(5,'education',{'degree':degree},'degree',degree,[source]);fact(5,'education',{'degree':degree},'institution','Visvesvaraya Technological University',['e8:0:38' if 'Master' in degree else 'e8:82:120'])
assert len(facts)==len({f['id'] for f in facts})
(OUT/'reference-facts.json').write_text(json.dumps({'method':'AI analyst reference from saved source blocks, frozen before LLM mapping; not human/PDF verified',
 'facts':facts,'ambiguous_or_absent_controls':[
 {'document':1,'field':'Godavari Cuts role','expectation':'No role explicitly provided; empty required role is appropriate, not a mapping omission.'},
 {'document':1,'field':'B.Com institution','expectation':'Institution could be shared with MBA but the association is not explicit; abstention is acceptable.'},
 {'document':2,'field':'languages','expectation':'Programming languages belong to skills, not spoken languages; no spoken languages stated.'},
 {'document':3,'field':'education years','expectation':'Detached 2022/2018/2016 may correspond by order; uncertainty must be disclosed rather than asserted from local labels.'},
 {'document':3,'field':'Besant Technologies trainee','expectation':'Explicit training role; employment versus training representation is policy-ambiguous.'},
 {'document':5,'field':'contact.email','expectation':'Two distinct emails occur; either may be supported, preferred email is ambiguous.'},
 {'document':5,'field':'education dates and Siemens dates','expectation':'Detached dates and source ordering make associations uncertain; do not score guessed date associations as ground truth.'},
 {'document':5,'field':'publications/membership/awards','expectation':'No dedicated target slots; preserve as unmapped notes, not invented certifications.'}]
},ensure_ascii=False,indent=2)+'\n')
print('Frozen critical scalar field opportunities:',len(facts),'by document:',{i:sum(f['document']==i for f in facts) for i in range(1,6)})
