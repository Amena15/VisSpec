// Simple test to verify the traceability save functionality
// This file can be run in the browser console to test the save function

// Test function to verify the save functionality
function testTraceabilitySave() {
  console.log('Testing traceability save functionality...');
  
  // Check if we're on the traceability page
  if (!window.location.pathname.includes('/traceability/')) {
    console.error('Not on traceability page. Please navigate to a project traceability page first.');
    return;
  }
  
  // Check if the traceability component is loaded
  const addNoteButtons = document.querySelectorAll('button:contains("Add Note")');
  if (addNoteButtons.length === 0) {
    console.error('No "Add Note" buttons found. Make sure there are requirements in the table.');
    return;
  }
  
  // Test 1: Click the first "Add Note" button
  console.log('Test 1: Clicking "Add Note" button...');
  addNoteButtons[0].click();
  
  // Wait for modal to appear
  setTimeout(() => {
    const modal = document.querySelector('.fixed.inset-0');
    if (!modal) {
      console.error('Modal did not appear after clicking "Add Note"');
      return;
    }
    
    console.log('✓ Modal appeared successfully');
    
    // Test 2: Check if textarea exists and is empty
    const textarea = modal.querySelector('textarea');
    if (!textarea) {
      console.error('Textarea not found in modal');
      return;
    }
    
    if (textarea.value !== '') {
      console.error('Textarea is not empty when modal opens');
      return;
    }
    
    console.log('✓ Textarea is empty and ready for input');
    
    // Test 3: Enter test text
    const testText = 'This is a test note for traceability functionality.';
    textarea.value = testText;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    
    setTimeout(() => {
      if (textarea.value !== testText) {
        console.error('Textarea value was not updated correctly');
        return;
      }
      
      console.log('✓ Textarea accepts input correctly');
      
      // Test 4: Click save button
      const saveButton = modal.querySelector('button:contains("Save Note")');
      if (!saveButton) {
        console.error('Save button not found in modal');
        return;
      }
      
      console.log('Test 4: Clicking save button...');
      saveButton.click();
      
      // Check for success message
      setTimeout(() => {
        const toastElements = document.querySelectorAll('[role="alert"]');
        let successMessage = false;
        
        toastElements.forEach(el => {
          if (el.textContent.includes('Note saved successfully')) {
            successMessage = true;
          }
        });
        
        if (successMessage) {
          console.log('✓ Save functionality works correctly!');
          console.log('✓ Success message displayed');
          console.log('✓ All tests passed!');
        } else {
          console.error('Save operation may have failed - no success message found');
        }
      }, 2000);
      
    }, 100);
    
  }, 500);
}

// Instructions for running the test
console.log(`
To test the traceability save functionality:
1. Navigate to a project traceability page (e.g., /traceability/[project-id])
2. Make sure there are requirements in the table
3. Run: testTraceabilitySave()
4. Follow the console output to see the test results
`);
