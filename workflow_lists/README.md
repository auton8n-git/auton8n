# Workflow Categories

## Production Ready

Workflows hoàn toàn sẵn sàng để dùng trong production

**Count:** 1957 workflows

**File:** `production_ready.txt`

✅ **Recommendation:** Import trực tiếp vào n8n

---

## Needs Trigger

Workflows hợp lệ nhưng cần thêm trigger để tự động hóa

**Count:** 28 workflows

**File:** `needs_trigger.txt`

⚠️ **Recommendation:** Thêm trigger node trước khi deploy

---

## Cloud Incompatible

Workflows dùng file system - chỉ hoạt động trên self-hosted

**Count:** 38 workflows

**File:** `cloud_incompatible.txt`

☁️ **Recommendation:** Refactor để tương thích cloud hoặc dùng self-hosted

---

## Security Risk

Workflows dùng executeCommand - không khuyến khích

**Count:** 23 workflows

**File:** `security_risk.txt`

🔒 **Recommendation:** Refactor thành Code node hoặc API calls

---

## Corrupted

Workflows bị lỗi JSON - KHÔNG THỂ DÙNG

**Count:** 0 workflows

**File:** `corrupted.txt`

❌ **Recommendation:** Xóa bỏ hoặc re-export từ n8n gốc

---

