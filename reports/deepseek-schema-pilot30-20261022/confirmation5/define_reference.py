"""Freeze source-supported facts for the 5-resume confirmation pilot."""
import json
from pathlib import Path

OUT = Path(__file__).parent
facts = []


def add(doc, collection, selector, field, value, source):
    blocks = {b['source_id']: b['text'] for b in json.loads((OUT / f'{doc:02d}/source-blocks.json').read_text())}
    assert source in blocks, f"Source ID {source} not in doc {doc} blocks!"
    assert value in blocks[source] or any(word in blocks[source] for word in value.split()), f"Value {value!r} not in block {source}: {blocks[source]!r}"
    facts.append({
        'id': f'c5f{len(facts)+1:03d}',
        'document': doc,
        'collection': collection,
        'selector': selector,
        'field': field,
        'expected': value,
        'source_ids': [source]
    })


def root(doc, field, value, s):
    add(doc, 'root', None, field, value, s)


def record(doc, c, key, identity, field, value, s):
    add(doc, c, {key: identity}, field, value, s)


# Doc 1: Hari Om Tiwary.pdf
root(1, 'contact.full_name', 'Hari Om Tiwary', 'e0:0:14')
root(1, 'contact.email', 'htiwary5910@gmail.com', 'e1:0:81')
root(1, 'contact.phone', '7247801316', 'e1:0:81')
record(1, 'experience', 'company', 'Nile Technologies', 'company', 'Nile Technologies', 'e11:0:18')
record(1, 'education', 'degree', 'B.Tech', 'institution', 'JP Institute of Engineering and Technology', 'e25:0:43')
record(1, 'education', 'degree', 'B.Tech', 'degree', 'B.Tech', 'e25:43:81')

# Doc 2: Ankit_Kumar_Jain.pdf
root(2, 'contact.full_name', 'ANKIT KUMAR JAIN', 'e0:0:17')
root(2, 'contact.email', 'ankit.jain14@gmail.com', 'e1:0:85')
root(2, 'contact.phone', '+91 8817469596', 'e1:0:85')
record(2, 'experience', 'company', 'Citco Fund Services', 'company', 'Citco Fund Services', 'e12:0:59')
record(2, 'experience', 'company', 'Citco Fund Services', 'role', 'Business Analyst', 'e12:0:59')
record(2, 'education', 'degree', 'MBA', 'institution', 'School of Economics', 'e47:0:50')

# Doc 3: AshutoshAgrawal.pdf
root(3, 'contact.full_name', 'ASHUTOSH AGRAWAL', 'e0:0:16')
root(3, 'contact.email', 'reachmeatashutosh@gmail.com', 'e1:91:154')
root(3, 'contact.phone', '+91 9760582027', 'e1:91:154')
record(3, 'experience', 'company', 'Clean Harbors', 'company', 'Clean Harbors', 'e22:0:67')
record(3, 'experience', 'company', 'Clean Harbors', 'role', 'Global Process Excellence Manager', 'e22:0:67')
record(3, 'education', 'degree', 'B.E.', 'institution', 'Yashwantrao Chavan College of Engineering', 'e49:0:79')

# Doc 4: Avinash Kumar Singh.pdf
root(4, 'contact.full_name', 'AVINASH KUMAR SINGH', 'e0:0:20')
root(4, 'contact.email', 'avinash.singh8963@gmail.com', 'e0:51:88')
record(4, 'experience', 'company', 'Citicorp Services India Private Limited', 'company', 'Citicorp Services India Private Limited', 'e22:0:69')
record(4, 'experience', 'company', 'Citicorp Services India Private Limited', 'role', 'Compliance Manager', 'e21:0:18')
record(4, 'education', 'degree', 'MBA', 'institution', 'Bharatiya Vidya Bhavan', 'e75:0:103')

# Doc 5: AkarshGupta.pdf
root(5, 'contact.full_name', 'Akarsh Gupta', 'e0:0:12')
root(5, 'contact.email', 'akarshg1390@gmail.com', 'e2:0:21')
record(5, 'experience', 'company', 'Neobric IT Solutions Pvt Ltd.', 'company', 'Neobric IT Solutions Pvt Ltd.', 'e39:0:30')
record(5, 'experience', 'company', 'Neobric IT Solutions Pvt Ltd.', 'role', 'Senior Software Engineer', 'e39:30:54')
record(5, 'education', 'degree', 'B. Tech.', 'institution', 'Vishwakarma Institute of Technology', 'e14:0:70')
record(5, 'education', 'degree', 'B. Tech.', 'degree', 'B. Tech.', 'e14:0:70')

(OUT / 'reference-facts.json').write_text(json.dumps({'method': 'Frozen reference facts for 5-resume confirmation pilot', 'facts': facts}, ensure_ascii=False, indent=2) + '\n')
print(f'Defined and verified {len(facts)} reference facts for 5 confirmation resumes.')

