🏗️ Architecture — Microservices
Monolith mat banao. Alag-alag services:
ServiceKaamauth-serviceLogin, JWT, OAuthuser-serviceStudent & Faculty profilesform-servicePreference submission & validationmatching-serviceAllocation algorithmnotification-serviceEmail / SMS / In-appadmin-serviceDashboard, overrides, exportsanalytics-serviceReports, trends
API Gateway (Kong / Nginx) sab ke aage baithega.

👤 Auth Module — Hardcore

SSO via college LDAP / Google Workspace (college email se auto-login)
JWT + Refresh Token rotation
RBAC — Student / Guide / HOD / Admin / Super Admin
2FA optional (TOTP)
Session management with Redis
Audit log — kisne kab kya kiya


🎓 Student Side — Full Featured

Onboarding flow:

Area of interest tags select karo
Upload SOP (Statement of Purpose) PDF
CGPA auto-fetch from college ERP (API integration)


Smart Guide Recommendations — AI-based, based on:

Research area match
Past project topics
Guide's publication keywords (NLP match)


Preference form:

Drag & drop ranking (not just 1-2-3)
Real-time seat availability counter
"Guide is almost full" warning


Status page with timeline view — form submitted → under review → matched → confirmed
In-app chat request to guide (pre-acceptance)


👨‍🏫 Guide/Faculty Side

Dashboard with analytics:

Applicant quality score (based on CGPA + SOP + area match)
Comparison view of all applicants


Shortlisting tools — filter by CGPA, interest area
Accept / Reject / Waitlist with reason
Set dynamic capacity (can update until deadline)
Calendar integration — availability slots for initial meeting
Guide profile CMS — research areas, current projects, publications (auto-fetch from Google Scholar API)


🛠️ Admin Panel — God Mode

Full allocation override — drag student from one guide to another
Batch operations — bulk assign unmatched students
Deadline management with countdown timer
Form versioning — agar form ka format change karna ho
Conflict resolution dashboard — red-flag cases dikhega
Export:

Excel (.xlsx) — full allotment sheet
PDF — official signed allotment letter (auto-generated)
JSON — ERP sync ke liye


Broadcast announcements (email + in-app)


🧠 Matching Algorithm — Core Engine
Phase 1 — Preference-Based Greedy

Students ranked by priority score:

CGPA weight
SOP quality score (NLP)
Early submission bonus


Allocate in order: 1st pref → 2nd → 3rd

Phase 2 — Stable Matching (Gale-Shapley)

Students + Guides dono ki preference list
Stable pairing guarantee — no student-guide pair exists who'd both prefer each other over current match
Handle unmatched students separately

Phase 3 — Admin Override + Manual Cleanup

Remaining unmatched → admin manually assigns

Edge Cases handled:

Guide leaves mid-process → re-allocation trigger
Student withdraws → slot opens up, waitlist activates
All 3 preferences full → fallback pool


🔔 Notification Service

Email (SendGrid / AWS SES) — templates for every event
SMS (Twilio) — critical alerts only
In-app notifications — real-time via WebSockets
Notification preferences — student choose kare kya chahiye


📊 Analytics & Reporting

Admin dashboard:

Allotment completion % (live)
Most preferred guides (heatmap)
Guide load distribution chart
Historical trends — previous batches


Exportable reports for HOD/Dean
Anomaly detection — e.g., one guide getting 80% of requests


🔗 Integrations
External SystemPurposeCollege ERPAuto-fetch student data, CGPAGoogle Scholar APIGuide's publication dataGoogle CalendarMeeting schedulingLDAP / Azure ADSSO loginS3 / Cloudflare R2SOP PDF storage

💻 Tech Stack
Frontend       → Next.js 14 (App Router) + Tailwind + shadcn/ui
Backend        → Node.js (Express) or Django (Python)
Realtime       → Socket.io / Supabase Realtime
Database       → PostgreSQL (primary) + Redis (cache/sessions)
Search         → Elasticsearch (guide search, SOP indexing)
Queue          → BullMQ / RabbitMQ (notifications, matching job)
Storage        → AWS S3 (SOPs, exports)
Auth           → NextAuth / Keycloak (SSO)
Deployment     → Docker + Kubernetes
CI/CD          → GitHub Actions
Monitoring     → Grafana + Prometheus + Sentry

🗂️ Database Schema (Key Tables)
users           → id, role, name, email, department
students        → user_id, cgpa, area_of_interest[], sop_url
guides          → user_id, capacity, research_areas[], scholar_id
preferences     → student_id, [guide_id_1, guide_id_2, guide_id_3], submitted_at
allocations     → student_id, guide_id, status, allocated_at, method (auto/manual)
notifications   → user_id, type, message, read, created_at
audit_logs      → actor_id, action, target, timestamp, metadata

🔐 Security

Rate limiting on all endpoints
Input sanitization + XSS protection
File upload validation (SOP PDF — type + size check)
OWASP Top 10 coverage
Role permission matrix — har endpoint pe check


📱 Bonus — Mobile App (Optional)

React Native — same API consume karega
Push notifications
Status tracking on phone