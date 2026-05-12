// Test script to debug the save note functionality
// Run this in the browser console on the traceability page

async function testSaveNote() {
  console.log('=== Testing Save Note Functionality ===');
  
  // Check if we're on the traceability page
  if (!window.location.pathname.includes('/traceability/')) {
    console.error('❌ Not on traceability page. Please navigate to a project traceability page first.');
    return;
  }
  
  // Find the first "Add Note" button
  const addNoteButtons = Array.from(document.querySelectorAll('button')).filter(btn => 
    btn.textContent.includes('Add Note')
  );
  
  if (addNoteButtons.length === 0) {
    console.error('❌ No "Add Note" buttons found. Make sure there are requirements in the table.');
    return;
  }
  
  console.log('✅ Found Add Note buttons');
  
  // Click the first "Add Note" button
  console.log('📝 Clicking Add Note button...');
  addNoteButtons[0].click();
  
  // Wait for modal to appear
  setTimeout(() => {
    const modal = document.querySelector('.fixed.inset-0');
    if (!modal) {
      console.error('❌ Modal did not appear after clicking "Add Note"');
      return;
    }
    
    console.log('✅ Modal appeared successfully');
    
    // Find the textarea
    const textarea = modal.querySelector('textarea');
    if (!textarea) {
      console.error('❌ Textarea not found in modal');
      return;
    }
    
    // Enter test text
    const testText = `Test note for debugging - ${new Date().toISOString()}`;
    textarea.value = testText;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    
    console.log('📝 Entered test text:', testText);
    
    // Find and click the save button
    const saveButton = Array.from(modal.querySelectorAll('button')).find(btn => 
      btn.textContent.includes('Save Note')
    );
    
    if (!saveButton) {
      console.error('❌ Save button not found in modal');
      return;
    }
    
    console.log('💾 Clicking Save Note button...');
    saveButton.click();
    
    // Wait for the operation to complete
    setTimeout(() => {
      // Check for success message
      const toastElements = document.querySelectorAll('[role="alert"]');
      let successMessage = false;
      let errorMessage = false;
      
      toastElements.forEach(el => {
        const text = el.textContent;
        if (text.includes('Note saved successfully')) {
          successMessage = true;
          console.log('✅ Success message found:', text);
        } else if (text.includes('Failed to save note')) {
          errorMessage = true;
          console.log('❌ Error message found:', text);
        }
      });
      
      if (successMessage) {
        console.log('🎉 Save note test PASSED!');
      } else if (errorMessage) {
        console.log('❌ Save note test FAILED!');
        console.log('🔍 Check the browser console for detailed error information');
        console.log('🔍 Check the Network tab for the failed request');
      } else {
        console.log('⚠️ No success or error message found - operation may still be in progress');
      }
      
    }, 3000);
    
  }, 1000);
}

// Instructions
console.log(`
To test the save note functionality with debugging:
1. Navigate to a project traceability page (e.g., /traceability/[project-id])
2. Make sure you're logged in and there are requirements in the table
3. Open the browser console (F12)
4. Run: testSaveNote()
5. Watch the console output and Network tab for detailed debugging information
6. Check for any authentication errors or request payload issues
`);
