import requests
import json

emails = [
    "From: andy.fastow@enron.com\nSubject: Budget Constraints\n\nEngineering headcount is frozen. We cannot add the reporting module to Phase 1. Must defer to Phase 2.",
    "From: kenneth.lay@enron.com\nSubject: Q4 Platform Strategy\n\nWe must launch the trading platform by December 31st. Authentication is the critical path. SSO is non-negotiable for enterprise clients.",
    "From: louise.kitchen@enron.com\nSubject: Performance Requirements\n\nThe platform must handle 50000 concurrent users during peak trading hours. Current estimate of 10000 is insufficient.",
    "From: kenneth.lay@enron.com\nSubject: Mobile Access\n\nBoard requires mobile access for executives. iOS and Android apps needed. This adds to scope significantly.",
    "From: jeff.skilling@enron.com\nSubject: Security Mandate\n\nAll financial transactions must be encrypted with AES-256. Compliance team requires full audit logging. No exceptions.",
    "From: andy.fastow@enron.com\nSubject: Re: Security Mandate\n\nAudit logging will require additional database capacity. Current Postgres setup cannot handle this without significant cost.",
    "From: jeff.skilling@enron.com\nSubject: Re: Mobile Access\n\nMobile is out of scope for Phase 1. Kenneth and I disagree on this. Need resolution by Friday.",
    "From: kenneth.lay@enron.com\nSubject: Re: Performance Requirements\n\nLouise is correct. 50000 concurrent users minimum. This is a hard requirement from the board.",
    "From: louise.kitchen@enron.com\nSubject: Dashboard Requirements\n\nTraders need real-time P&L display. Data refresh must be under 500ms. Export to Excel and PDF mandatory.",
    "From: jeff.skilling@enron.com\nSubject: Re: Q4 Platform Strategy\n\nAgreed on SSO. However engineering says December 31st is unrealistic. Proposing January 15th for Phase 1 auth only."
]

for email in emails:
    res = requests.post("http://localhost:8001/ingest/email", json={"text": email})
    print(res.text)
