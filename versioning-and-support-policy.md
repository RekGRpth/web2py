# web2py Versioning, Release, and Support Policy

_Last updated: 2025-12-20_

This document defines the official **release process**, **versioning scheme**, **support status**, and **end-of-life (EOL) policy** for **web2py**.  
It is intended to provide clear, unambiguous guidance to users, contributors, auditors, and downstream consumers.

---

## 1. Project Status (Important)

⚠️ **web2py is in limited maintenance mode and is no longer recommended for new projects.**

- web2py will not receive new features.
- Only **limited, best-effort maintenance** may occur.
- Users are **strongly encouraged to migrate** to **py4web**, the official successor.

**Recommended successor:**  

    https://py4web.com

py4web is smaller, significantly faster, actively developed, and compatible with web2py’s:
- Templates
- pydal database layer
- Core concepts  
Porting existing applications is typically straightforward.

---

## 2. Versioning Scheme

web2py follows **Semantic Versioning (SemVer)** with additional constraints based on Python compatibility.

### Version Format

    MAJOR.MINOR.PATCH

### Version Compatibility

| Major Version | Python Support | Notes |
|--------------|---------------|------|
| 2.x.x | Python 2.7 | **End of Life** |
| 3.x.x | Python ≥ 3.9 | Limited maintenance |

- **v2.27.1** is the **final release supporting Python 2.7**
- All **3.x.x** releases require **Python 3.9 or newer**

### Breaking Changes

- Major version changes are primarily tied to **Python version compatibility**
- Historically, web2py has avoided introducing breaking changes outside of Python transitions
- If unavoidable breaking changes were ever required, they would:
  - Be clearly documented
  - Trigger a new major version
  - Be announced in advance via official channels

---

## 3. Release Notification Process

### When a Release Occurs
When a new version of web2py is released:

1. A **GitHub release** is published
2. The release is **announced to the community**

### Notification Channels

Official release announcements are made via:
- **Google Group**:  
  https://groups.google.com/g/web2py
- **GitHub Releases & Tags**:  
  https://github.com/web2py/web2py/releases  
  https://github.com/web2py/web2py/tags

Announcements include:
- Version number
- Summary of changes
- Security relevance (if applicable)
- Link to release notes and commits

---

## 4. Support Policy

### Supported Versions

| Version | Status | Support Level |
|-------|--------|---------------|
| 2.27.1 | EOL | No support |
| 3.x.x (latest minor) | Limited | Best-effort fixes only |

### Definition of “Limited Support”

Limited support means:

Support May include:
- Critical bug fixes
- Severe security fixes (best effort)

Support Will NOT include:
- New features
- Performance improvements
- Backports to older release lines
- Guaranteed response times
- Long-term support commitments

Support may cease entirely at any time.

---

## 5. End-of-Life (EOL) Policy

### End-of-Life Criteria

A version is considered **End of Life** when:

- It is no longer maintained
- It receives no bug or security fixes
- Users must upgrade or migrate

### Current EOL Versions

- **All web2py 2.x releases**, including **2.27.1**, are **EOL**

### EOL Announcements

- EOL events are announced via:
  - Google Group
  - Prominent notice on https://web2py.com
- The homepage notice explicitly states:
  - Python 2 support has ended
  - Future development is discouraged

---

## 6. Security & CVE Handling

### Security Fixes

- Security fixes are released publicly via GitHub
- Releases addressing security issues are clearly identifiable in:
  - GitHub release notes
  - Associated commits

**Example:**  

Release `v2.24.1` includes a security-related fix:  
https://github.com/web2py/web2py/releases/tag/v2.24.1

### Private Disclosure

- web2py **does not maintain a private security embargo process**
- Vulnerabilities are fixed and disclosed publicly
- Users relying on web2py must monitor official release channels

---

## 7. Backporting Policy

web2py **does not backport fixes**.

- Fixes are applied only to the latest supported release line
- Older versions do not receive patches once superseded
- This policy reinforces the importance of upgrading or migrating

---

## 8. Migration Recommendation

Given web2py’s limited maintenance status:

**All users are strongly encouraged to migrate to py4web**

Benefits include:
- Active development
- Improved performance
- Modern Python support
- Easier long-term maintenance

Migration assistance is available via:
- py4web Google Group
- Community support channels

---

## 9. Summary

- web2py is in **limited maintenance mode**
- No new features will be added
- Only best-effort critical fixes may occur
- No backporting or long-term support guarantees
- Users should migrate to **py4web**

This document represents the authoritative policy for web2py versioning, releases, and support.

