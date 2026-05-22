(function () {
  "use strict";

  const pageDataElement = document.getElementById("page-data");

  window.pageData = {};

  if (pageDataElement) {
    try {
      window.pageData = JSON.parse(pageDataElement.textContent || "{}");
    } catch (error) {
      console.error("อ่าน pageData ไม่สำเร็จ:", error);
      window.pageData = {};
    }
  }

  const data = window.pageData || {};
  const catalog = Array.isArray(data.catalog) ? data.catalog : [];

  /* =========================================================
     SIDEBAR MOBILE
  ========================================================= */

  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");

  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  /* =========================================================
     CUSTOMER SEARCH
  ========================================================= */

  const customerSearch = document.getElementById("customerSearch");
  const customersTable = document.getElementById("customersTable");

  if (customerSearch && customersTable) {
    customerSearch.addEventListener("input", function () {
      const keyword = this.value.toLowerCase().trim();
      const rows = customersTable.querySelectorAll("tbody tr");

      rows.forEach(function (row) {
        row.style.display = row.textContent.toLowerCase().includes(keyword) ? "" : "none";
      });
    });
  }

  /* =========================================================
     PURCHASE PAGE
  ========================================================= */

  const typeSelect = document.getElementById("type_code");
  const subtypeSelect = document.getElementById("subtype_id");
  const unitPriceInput = document.getElementById("unit_price");
  const weightInput = document.getElementById("weight_kg");
  const totalInput = document.getElementById("total_amount");
  const customerSelect = document.getElementById("customer_id");

  const previewCustomer = document.getElementById("previewCustomer");
  const previewType = document.getElementById("previewType");
  const previewSubtype = document.getElementById("previewSubtype");
  const previewUnitPrice = document.getElementById("previewUnitPrice");
  const previewWeight = document.getElementById("previewWeight");
  const previewTotal = document.getElementById("previewTotal");

  function normalizeTypeCode(item) {
    return item.code || item.type_code || item.typeCode || "";
  }

  function normalizeTypeName(item) {
    return item.full_name || item.type_name_en || item.fullName || normalizeTypeCode(item);
  }

  function normalizeSubtypeId(sub) {
    return sub.id || sub.subtype_id || sub.subtypeId || "";
  }

  function normalizeSubtypeName(sub) {
    return sub.name || sub.subtype_name || sub.subtypeName || "";
  }

  function normalizeSubtypePrice(sub) {
    return Number(sub.price || sub.unit_price || sub.unitPrice || 0);
  }

  function getSelectedText(selectElement) {
    if (
      !selectElement ||
      !selectElement.selectedOptions ||
      !selectElement.selectedOptions[0]
    ) {
      return "-";
    }

    const text = selectElement.selectedOptions[0].textContent.trim();

    if (!text || text.includes("--")) {
      return "-";
    }

    return text;
  }

  function populateTypes() {
    if (!typeSelect) return;

    typeSelect.innerHTML = '<option value="">-- เลือกประเภทหลัก --</option>';

    if (!catalog.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "ไม่พบข้อมูลประเภทพลาสติกในฐานข้อมูล";
      option.disabled = true;
      typeSelect.appendChild(option);
      return;
    }

    catalog.forEach(function (item) {
      const typeCode = normalizeTypeCode(item);
      const typeName = normalizeTypeName(item);

      if (!typeCode) return;

      const option = document.createElement("option");
      option.value = typeCode;
      option.textContent = typeCode;
      option.title = typeName;

      typeSelect.appendChild(option);
    });
  }

  function populateSubtypes(typeCode) {
    if (!subtypeSelect) return;

    subtypeSelect.innerHTML = '<option value="">-- เลือกประเภทย่อย --</option>';

    if (!typeCode) {
      updatePurchaseSummary();
      return;
    }

    const selectedType = catalog.find(function (item) {
      return normalizeTypeCode(item) === typeCode;
    });

    if (!selectedType || !Array.isArray(selectedType.subtypes) || !selectedType.subtypes.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "ไม่พบประเภทย่อย";
      option.disabled = true;
      subtypeSelect.appendChild(option);
      updatePurchaseSummary();
      return;
    }

    selectedType.subtypes.forEach(function (sub) {
      const subtypeId = normalizeSubtypeId(sub);
      const subtypeName = normalizeSubtypeName(sub);
      const subtypePrice = normalizeSubtypePrice(sub);

      if (!subtypeId || Number.isNaN(Number(subtypeId))) {
        console.warn("ข้าม subtype เพราะ subtype_id ไม่ใช่ตัวเลข:", sub);
        return;
      }

      const option = document.createElement("option");
      option.value = subtypeId;
      option.textContent = subtypeName || "ไม่ระบุชื่อประเภทย่อย";
      option.dataset.price = String(subtypePrice);
      option.dataset.code = sub.code || sub.subtype_code || "";

      subtypeSelect.appendChild(option);
    });

    updatePurchaseSummary();
  }

  function updatePurchaseSummary() {
    if (!previewCustomer) return;

    const customerText = getSelectedText(customerSelect);
    const typeText = getSelectedText(typeSelect);
    const subtypeText = getSelectedText(subtypeSelect);

    const unitPrice = Number(unitPriceInput ? unitPriceInput.value || 0 : 0);
    const weight = Number(weightInput ? weightInput.value || 0 : 0);
    const total = unitPrice * weight;

    if (totalInput) {
      totalInput.value = total.toFixed(2);
    }

    if (previewCustomer) previewCustomer.textContent = customerText;
    if (previewType) previewType.textContent = typeText;
    if (previewSubtype) previewSubtype.textContent = subtypeText;
    if (previewUnitPrice) previewUnitPrice.textContent = "฿ " + unitPrice.toFixed(2);
    if (previewWeight) previewWeight.textContent = weight.toFixed(2) + " กก.";
    if (previewTotal) previewTotal.textContent = "฿ " + total.toFixed(2);
  }

  if (typeSelect && subtypeSelect) {
    populateTypes();

    typeSelect.addEventListener("change", function () {
      populateSubtypes(this.value);

      if (unitPriceInput) {
        unitPriceInput.value = "";
      }

      if (totalInput) {
        totalInput.value = "";
      }

      updatePurchaseSummary();
    });

    subtypeSelect.addEventListener("change", function () {
      const selectedOption = this.selectedOptions && this.selectedOptions[0];

      if (selectedOption && unitPriceInput) {
        const price = Number(selectedOption.dataset.price || 0);
        unitPriceInput.value = price.toFixed(2);
      }

      updatePurchaseSummary();
    });

    if (weightInput) {
      weightInput.addEventListener("input", updatePurchaseSummary);
      weightInput.addEventListener("change", updatePurchaseSummary);
    }

    if (customerSelect) {
      customerSelect.addEventListener("input", updatePurchaseSummary);
      customerSelect.addEventListener("change", updatePurchaseSummary);
    }
  }

  /* =========================================================
     RECEIPT PRINT
  ========================================================= */

  const printReceiptBtn = document.getElementById("printReceiptBtn");

  if (printReceiptBtn) {
    printReceiptBtn.addEventListener("click", function () {
      window.print();
    });
  }

  /* =========================================================
     AI IMAGE PREVIEW + PREDICT
  ========================================================= */

  const aiDetectForm = document.getElementById("aiDetectForm");
  const plasticImage = document.getElementById("plasticImage");
  const imagePreviewBox = document.getElementById("imagePreviewBox");
  const aiType = document.getElementById("aiType");
  const aiFullName = document.getElementById("aiFullName");
  const aiConfidence = document.getElementById("aiConfidence");
  const aiNote = document.getElementById("aiNote");
  const realAiBtn = document.getElementById("realAiBtn");

  function setAiResult(type, fullName, confidence, note) {
    if (aiType) aiType.textContent = type || "-";
    if (aiFullName) aiFullName.textContent = fullName || "-";
    if (aiConfidence) aiConfidence.textContent = confidence || "-";
    if (aiNote) aiNote.textContent = note || "-";
  }

  function setAiButtonLoading(isLoading) {
    if (!realAiBtn) return;

    realAiBtn.disabled = isLoading;
    realAiBtn.innerHTML = isLoading
      ? '<i class="bi bi-hourglass-split"></i> กำลังวิเคราะห์...'
      : '<i class="bi bi-stars"></i> วิเคราะห์รูปภาพ';
  }

  function resetImagePreview() {
    if (!imagePreviewBox) return;

    imagePreviewBox.innerHTML = `
      <div class="ai-upload-empty">
        <div class="ai-upload-circle">
          <i class="bi bi-image"></i>
        </div>
        <strong id="uploadFileName">คลิกเพื่อเลือกรูปภาพ</strong>
        <span>รองรับไฟล์ JPG, PNG หรือรูปภาพทั่วไป</span>
      </div>
    `;
  }

  if (plasticImage && imagePreviewBox) {
    plasticImage.addEventListener("change", function (event) {
      const file = event.target.files && event.target.files[0];

      if (!file) {
        resetImagePreview();
        setAiResult("-", "-", "-", "รออัปโหลดรูปภาพ");
        return;
      }

      if (!file.type.startsWith("image/")) {
        alert("กรุณาเลือกไฟล์รูปภาพเท่านั้น");
        plasticImage.value = "";
        resetImagePreview();
        setAiResult("-", "-", "-", "ไฟล์ไม่ถูกต้อง");
        return;
      }

      const reader = new FileReader();

      reader.onload = function (e) {
        imagePreviewBox.innerHTML = `
          <div class="ai-preview-wrap">
            <img src="${e.target.result}" alt="preview">
            <div class="ai-file-info">
              <i class="bi bi-check-circle-fill"></i>
              <span>${file.name}</span>
            </div>
          </div>
        `;
      };

      reader.readAsDataURL(file);
      setAiResult("-", "-", "-", "พร้อมวิเคราะห์รูปภาพ");
    });
  }

  async function predictPlastic() {
    if (!plasticImage || !plasticImage.files || !plasticImage.files[0]) {
      alert("กรุณาเลือกรูปภาพก่อน");
      setAiResult("-", "-", "-", "กรุณาเลือกรูปภาพก่อนวิเคราะห์");
      return;
    }

    const formData = new FormData();
    formData.append("image", plasticImage.files[0]);

    setAiButtonLoading(true);
    setAiResult("-", "-", "-", "กำลังส่งรูปภาพไปวิเคราะห์...");

    try {
      const response = await fetch("/api/predict_plastic", {
        method: "POST",
        body: formData,
        credentials: "same-origin",
      });

      const contentType = response.headers.get("content-type") || "";

      if (!contentType.includes("application/json")) {
        throw new Error("API ไม่ได้ส่งข้อมูล JSON กลับมา อาจยังไม่ได้ login หรือ route ผิด");
      }

      const result = await response.json();

      if (!response.ok || result.success === false) {
        throw new Error(
          result.error ||
          result.message ||
          result.detail ||
          "ไม่สามารถวิเคราะห์รูปภาพได้"
        );
      }

      const plasticType = result.plastic_type || result.type || result.class_name || "-";
      const fullName = result.plastic_full_name || result.full_name || plasticType;
      const confidenceValue = Number(result.confidence || 0);
      const confidenceText = Number.isFinite(confidenceValue)
        ? confidenceValue.toFixed(2) + "%"
        : "-";

      setAiResult(
        plasticType,
        fullName,
        confidenceText,
        "วิเคราะห์สำเร็จ"
      );
    } catch (error) {
      console.error("AI prediction error:", error);
      setAiResult(
        "-",
        "-",
        "-",
        "เกิดข้อผิดพลาด: " + error.message
      );
    } finally {
      setAiButtonLoading(false);
    }
  }

  if (realAiBtn) {
    realAiBtn.addEventListener("click", predictPlastic);
  }

  if (aiDetectForm) {
    aiDetectForm.addEventListener("submit", function (event) {
      event.preventDefault();
      predictPlastic();
    });
  }
})();