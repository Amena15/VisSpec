# 🧪 VisSpec Frontend Testing Guide - Step by Step

## 📋 **Overview**
This guide provides step-by-step instructions to test the text extraction and validation functionality in the VisSpec frontend yourself.

---

## 🚀 **Step 1: Start the Application**

### **Start Backend Server**
```bash
cd /Users/amena/Documents/FYPCode/VisSpec/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **Start Frontend Server**
```bash
cd /Users/amena/Documents/FYPCode/VisSpec/frontend
npm run dev
```

### **Access the Application**
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 📄 **Step 2: Test Document Upload and Text Extraction**

### **2.1 Navigate to Document Upload**
1. Open http://localhost:5173 in your browser
2. Click on "Upload Document" or navigate to `/upload`
3. You should see the document upload interface

### **2.2 Test File Upload**
1. **Create a test document** with the following content:

**Create a test TXT file** (`test_requirements.txt`):
```
Virtual Clinic System Requirements

1. Introduction
This document describes requirements for the Virtual Clinic management system.

2. Functional Requirements

2.1 User Management
Maintain Specialities
Add Doctor
Update Doctor Profile
Delete Doctor
View Doctor List

2.2 Patient Management
Register Patient
Update Patient Information
View Patient History
Book Appointment
Cancel Appointment

3. Non-Functional Requirements
The system shall respond within 2 seconds.
The system must handle 1000 concurrent users.
The application should be available 99.9% of the time.
The system must ensure patient data confidentiality.
```

2. **Upload the file**:
   - Drag and drop the file onto the upload area
   - Or click "Browse Files" and select your test file
   - Select a project (or create a new one)
   - Click "Upload Document"

### **2.3 Verify Text Extraction**
1. **Check the upload results**:
   - You should see a success message
   - Note the number of requirements found
   - Click "Start Analysis" or navigate to the analysis page

2. **Verify extracted requirements**:
   - Navigate to the analysis results page
   - You should see the extracted requirements listed
   - Check that requirements from tables were extracted
   - Verify the text is clean (no merged modal verbs)

---

## 🤖 **Step 3: Test AI Validation**

### **3.1 Run Validation**
1. **Navigate to Analysis Results**:
   - From the upload page, click "Start Analysis"
   - Or navigate directly to `/analysis-results/{doc_id}`

2. **Click "Run Validation"**:
   - Look for the "Run Validation" button
   - Click it to start the AI validation process
   - Wait for the validation to complete

### **3.2 Review Validation Results**
1. **Check the validation summary**:
   - Look for the overall quality score
   - Review the defect statistics
   - Check the severity breakdown

2. **Examine individual defects**:
   - Click on defect cards to expand them
   - Review the defect descriptions
   - Check the suggested fixes
   - Verify confidence scores

---

## 🔧 **Step 4: Test Suggestion Application**

### **4.1 Apply Suggestions**
1. **Expand a defect card**:
   - Click on a defect to see details
   - Review the suggested fix

2. **Apply the suggestion**:
   - Click "Apply Suggestion"
   - Verify the requirement text is updated
   - Check that the defect is marked as resolved

### **4.2 Test Undo Functionality**
1. **Undo the change**:
   - Look for the "Undo" button or press Ctrl+Z
   - Click "Undo" to revert the change
   - Verify the original text is restored

2. **Test redo if available**:
   - Press Ctrl+Y to redo the change
   - Verify the suggestion is reapplied

---

## 📊 **Step 5: Test Enhanced Features**

### **5.1 Test PDF Table Extraction**
1. **Create a test PDF** with tables:
   - Create a document with requirement tables
   - Save as PDF
   - Upload the PDF file
   - Verify table content is extracted

### **5.2 Test DOCX Table Extraction**
1. **Create a test DOCX** with tables:
   - Create a Word document with requirement tables
   - Upload the DOCX file
   - Verify table content is extracted

### **5.3 Test Merged Modal Cleanup**
1. **Create a document with merged modals**:
   ```
   The system shallshould respond quickly.
   Users willmust authenticate before access.
   ```
2. **Upload and verify**:
   - Upload the document
   - Check that merged modals are fixed in the extracted text

---

## 🔍 **Step 6: Test Cross-Requirement Consistency**

### **6.1 Create Contradictory Requirements**
1. **Create a document with contradictions**:
   ```
   The system shall always allow users to delete their account.
   The system shall never allow users to delete their account.
   ```

2. **Upload and validate**:
   - Upload the document
   - Run validation
   - Verify inconsistency is detected

---

## 📱 **Step 7: Test Frontend Components**

### **7.1 Test Validation Results Component**
1. **Navigate to validation results**
2. **Verify the following**:
   - Defect cards are displayed correctly
   - Severity indicators are shown
   - Confidence scores are displayed
   - Expand/collapse functionality works

### **7.2 Test Validation Summary Component**
1. **Check the summary dashboard**:
   - Quality score visualization
   - Defect statistics
   - Severity breakdown
   - Status indicators

### **7.3 Test Defect Card Component**
1. **Interact with defect cards**:
   - Click to expand/collapse
   - Apply suggestions
   - Ignore defects
   - View original text

---

## 🛠️ **Step 8: Test API Integration**

### **8.1 Check Browser Console**
1. **Open browser developer tools**:
   - Press F12 or right-click → Inspect
   - Go to Console tab

2. **Look for API calls**:
   - Check for successful API requests
   - Verify no error messages
   - Check response data

### **8.2 Test API Endpoints Directly**
1. **Test health endpoint**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Test validation endpoint** (with authentication):
   ```bash
   curl -X POST http://localhost:8000/api/validation/validate \
   -H "Content-Type: application/json" \
   -d '{"text": "The system shall provide adequate performance."}'
   ```

---

## ✅ **Step 9: Verification Checklist**

### **Document Processing**
- [ ] File upload works for PDF, DOCX, TXT
- [ ] Text extraction is accurate
- [ ] Table content is extracted
- [ ] Merged modal verbs are fixed
- [ ] Document structure is identified

### **AI Validation**
- [ ] Validation runs successfully
- [ ] Defects are detected and classified
- [ ] Confidence filtering works (≥70%)
- [ ] Quality score is calculated
- [ ] Cross-requirement analysis works

### **User Interface**
- [ ] Validation results display correctly
- [ ] Defect cards are interactive
- [ ] Suggestions can be applied
- [ ] Undo/redo functionality works
- [ ] Error handling is proper

### **Business Rules**
- [ ] File type validation (BR-07)
- [ ] File size limits (BR-08)
- [ ] Confidence filtering (BR-10)
- [ ] State consistency (BR-14)
- [ ] Undo logging (BR-15)

---

## 🚨 **Step 10: Troubleshooting**

### **Common Issues**

1. **Upload fails with 403 error**:
   - Check if backend is running
   - Verify authentication is working
   - Check file size and type

2. **Validation doesn't run**:
   - Check if requirements were extracted
   - Verify GROQ_API_KEY is set (for LLM validation)
   - Check browser console for errors

3. **Suggestions don't apply**:
   - Check if user owns the requirement
   - Verify API endpoints are accessible
   - Check browser console for errors

4. **Frontend not loading**:
   - Check if frontend server is running
   - Verify backend is accessible
   - Check browser console for errors

### **Debug Tips**
- **Browser Console**: Check for JavaScript errors
- **Network Tab**: Monitor API requests and responses
- **Backend Logs**: Check terminal for error messages
- **Database**: Verify data is being stored correctly

---

## 🎯 **Success Criteria**

You have successfully tested the frontend if:

✅ **Document Upload**: Files upload and text is extracted correctly
✅ **AI Validation**: Validation runs and defects are detected
✅ **Suggestion Application**: Suggestions can be applied and undone
✅ **User Interface**: All components work as expected
✅ **Business Rules**: All validation rules are enforced
✅ **Error Handling**: Errors are handled gracefully

---

## 📞 **Need Help?**

If you encounter issues:

1. **Check the browser console** for error messages
2. **Verify both servers are running** (backend on port 8000, frontend on port 5173)
3. **Check the API documentation** at http://localhost:8000/docs
4. **Review the test results** in the database

---

**🎉 Happy Testing!**

This guide should help you thoroughly test all the frontend functionality and verify that everything is working correctly with the enhanced backend implementation.
