# Product Requirements Document (PRD)

## 1. Overview
**Product Name:** Job Portal Profile Refresh Automation  
**Author:** Product Manager  
**Date:**  
**Version:** v1.0

### 1.1 Purpose
Build a lightweight, serverless automation system to periodically update specific profile fields on selected job portals to keep the user profile "fresh" and improve recruiter visibility.

### 1.2 Background / Context
Job portals prioritize recently updated profiles in search and recommendations. Manual updates are repetitive and time-consuming. Existing portals do not provide APIs for lightweight profile refresh. This product automates minimal, non-disruptive profile updates for a single user across LinkedIn, Naukri, and Indeed using browser automation and AI-assisted content modification.

### 1.3 Goals & Objectives
- Automate profile refresh actions reliably
- Make minimal, non-intrusive content changes
- Ensure secure handling of credentials
- Provide auditability and notifications

### 1.4 Success Metrics (KPIs)
- Successful execution rate > 95%
- Zero credential leaks or security incidents
- 100% delivery of success/failure email notifications

---

## 2. Problem Statement
Manually updating job portal profiles daily is inefficient and error-prone. Since no official APIs exist for these updates, a controlled browser automation approach is required to reliably update specific profile sections without altering intent or meaning.

---

## 3. Target Users & Personas
| Persona | Description | Key Needs |
|-------|-------------|----------|
| Single Job Seeker | Individual maintaining active job profiles | Automation, reliability, privacy |

---

## 4. User Journeys & Use Cases
### 4.1 Primary Use Cases
- UC1: Update LinkedIn "About" section
- UC2: Update Naukri "Profile Summary"
- UC3: Update Indeed "Skills"

### 4.2 User Flow (High-level)
EventBridge trigger → Lambda execution → Retrieve secrets → Login via Playwright → Read existing field → AI modifies content slightly → Save update → Log outcome → Send email notification

---

## 5. Scope
### 5.1 In-Scope
- Automation for LinkedIn, Naukri, and Indeed
- Single-user execution model
- Static, predefined fields per portal
- Email notifications for success and failure
- Execution and audit logging

### 5.2 Out-of-Scope
- Multi-user support
- Job auto-apply
- Resume optimization
- UI dashboard
- Additional portals

---

## 6. Functional Requirements
| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| FR-1 | Scheduled Trigger | Lambda triggered via AWS EventBridge | High |
| FR-2 | Credential Management | Credentials stored and retrieved from AWS Secrets Manager | High |
| FR-3 | Portal Authentication | Login automation using Playwright | High |
| FR-4 | Content Read | Fetch current profile field content | High |
| FR-5 | AI Content Mutation | Use Amazon Bedrock to introduce minimal text changes | High |
| FR-6 | Profile Update | Save updated profile content successfully | High |
| FR-7 | Notification | Send success/failure email notification | High |
| FR-8 | Audit Logging | Persist per-portal execution logs | Medium |

---

## 7. Non-Functional Requirements
- **Performance:** Each portal update should complete within 2 minutes
- **Scalability:** Designed for single-user only
- **Security:** No plaintext credential logging; Secrets Manager only
- **Reliability:** One retry for transient failures
- **Compliance:** Best-effort, low-frequency automation

---

## 8. Data & Integration Requirements
- **AWS Services:** Lambda, EventBridge, Secrets Manager, CloudWatch, SES or SNS
- **Automation Framework:** Playwright (headless Chromium)
- **AI Provider:** Amazon Bedrock (text generation)
- **Logging:** CloudWatch Logs as audit trail

---

## 9. UX / UI Requirements
- No user interface in v1
- All configuration handled via code and AWS resources

---

## 10. Assumptions & Constraints
- CAPTCHA challenges may prevent successful login
- Indeed email OTP must be programmatically accessible
- Portal UI changes may break selectors

---

## 11. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| CAPTCHA challenges | Automation failure | Human-like delays, retries |
| Terms of Service | Account risk | Minimal changes, low frequency |
| UI selector changes | Runtime errors | AI-assisted selector fallback |
| OTP retrieval failure | Login failure | Timeout and failure notification |

---

## 12. Future Enhancements (Explicitly Out of Scope)
- Support for additional portals
- Resume or content optimization
- Job auto-apply features
- Multi-user support

