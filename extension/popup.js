document.addEventListener('DOMContentLoaded', function() {
  const titleInput = document.getElementById('title');
  const folderSelect = document.getElementById('folder');
  const tickerContainer = document.getElementById('tickerContainer');
  const tickerInput = document.getElementById('ticker');
  const addToQueueButton = document.getElementById('addToQueue');
  const processQueueButton = document.getElementById('processQueue');
  const refreshQueueButton = document.getElementById('refreshQueue');
  const clearQueueButton = document.getElementById('clearQueue');
  const queueListDiv = document.getElementById('queueList');
  const statusDiv = document.getElementById('status');

  // Load queue from storage
  let videoQueue = [];
  
  // Initialize the extension
  init();

  async function init() {
    try {
      // Add error handler for chrome APIs
      if (typeof chrome === 'undefined') {
        showStatus('Chrome APIs are not available. Please ensure you\'re running as a Chrome extension.', 'error');
        return;
      }

      // Load queue from storage
      try {
        videoQueue = await getQueueFromStorage();
      } catch (error) {
        console.error('Failed to load queue:', error);
        videoQueue = [];
        showStatus('Failed to load saved queue', 'error');
      }
      
      // Update UI based on queue
      updateQueueUI();
      
      // Get current tab info for pre-populating form
      try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.url && tab.url.includes('youtube.com/watch')) {
          // Get video title directly from the page
          try {
            chrome.scripting.executeScript({
              target: { tabId: tab.id },
              function: () => {
                // Try getting title from different possible elements
                const titleElement = document.querySelector('h1.title.style-scope.ytd-video-primary-info-renderer') || 
                                   document.querySelector('h1.ytd-video-primary-info-renderer') ||
                                   document.querySelector('title');
                
                return titleElement ? titleElement.textContent.trim() : '';
              }
            }, (results) => {
              if (results && results[0] && results[0].result) {
                titleInput.value = cleanTitle(results[0].result);
              } else {
                // Fallback to noembed API
                fetchTitleFromAPI(tab.url);
              }
            });
          } catch (error) {
            console.error('Error extracting title:', error);
            // Fallback to noembed API
            fetchTitleFromAPI(tab.url);
          }
        } else {
          showStatus('Please navigate to a YouTube video first', 'error');
        }
      } catch (error) {
        console.error('Error querying tabs:', error);
        showStatus('Failed to access current tab', 'error');
      }
    } catch (error) {
      console.error('Initialization error:', error);
      showStatus('Failed to initialize extension', 'error');
    }
  }
  
  // Fallback function to fetch title from API
  async function fetchTitleFromAPI(url) {
    try {
      const response = await fetch(`https://noembed.com/embed?url=${url}`);
      const data = await response.json();
      if (data && data.title) {
        titleInput.value = cleanTitle(data.title);
      }
    } catch (error) {
      console.error('Error fetching video info:', error);
    }
  }

  // Basic title cleaning for better filenames
  function cleanTitle(title) {
    // Replace special characters and emojis
    let cleaned = title
      .replace(/[^\w\s\-.,&()[\]]/g, '') // Keep only alphanumeric, spaces, and some punctuation
      .replace(/\s+/g, ' ')              // Replace multiple spaces with a single space
      .trim();
      
    // Truncate long titles
    if (cleaned.length > 80) {
      cleaned = cleaned.substring(0, 77) + '...';
    }
    
    return cleaned;
  }

  // Show/hide ticker input based on folder
  folderSelect.addEventListener('change', function() {
    tickerContainer.style.display = 
      folderSelect.value === 'Economics' ? 'block' : 'none';
    if (folderSelect.value !== 'Economics') {
      tickerInput.value = '';
    }
  });

  // Enable Enter key to add to queue
  titleInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      addToQueueButton.click();
    }
  });

  tickerInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      addToQueueButton.click();
    }
  });

  // Add to Queue button click handler
  addToQueueButton.addEventListener('click', async function() {
    try {
      // Get current tab URL
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.url || !tab.url.includes('youtube.com/watch')) {
        throw new Error('Please navigate to a YouTube video first');
      }

      if (!titleInput.value.trim()) {
        throw new Error('Please enter a title for the video');
      }

      if (folderSelect.value === 'Economics' && !tickerInput.value.trim()) {
        throw new Error('Please enter a ticker symbol for Economics videos');
      }
      
      // Check if this URL is already in the queue
      const videoId = new URL(tab.url).searchParams.get('v');
      const existingItem = videoQueue.find(item => {
        try {
          return new URL(item.url).searchParams.get('v') === videoId;
        } catch (e) {
          return false;
        }
      });
      
      if (existingItem) {
        if (!confirm('This video is already in the queue. Add it again?')) {
          return;
        }
      }

      // Add to queue
      const queueItem = {
        id: Date.now().toString(),
        url: tab.url,
        title: titleInput.value.trim(),
        folder: folderSelect.value,
        ticker_symbol: folderSelect.value === 'Economics' ? tickerInput.value.trim() : null,
        status: 'pending',
        addedAt: new Date().toISOString()
      };

      videoQueue.push(queueItem);
      await saveQueueToStorage();
      updateQueueUI();
      
      showStatus('Added to queue!', 'success');
      
      // Clear form
      titleInput.value = '';
      tickerInput.value = '';

    } catch (error) {
      showStatus(error.message, 'error');
    }
  });

  // Process Queue button click handler
  processQueueButton.addEventListener('click', async function() {
    if (videoQueue.length === 0) {
      showStatus('Queue is empty', 'error');
      return;
    }

    try {
      processQueueButton.disabled = true;
      showStatus('Processing queue...', 'loading');
      
      let processedCount = 0;
      let hasErrors = false;
      
      // Process items in queue sequentially
      for (let i = 0; i < videoQueue.length; i++) {
        const item = videoQueue[i];
        if (item.status === 'pending' || item.status === 'failed') {
          try {
            // Update status to processing
            item.status = 'processing';
            item.lastUpdated = new Date().toISOString();
            await saveQueueToStorage();
            updateQueueUI();
            
            // Prepare request data
            const data = {
              url: item.url,
              category: item.folder,
              ticker_symbol: item.ticker_symbol,
              custom_title: item.title // Send custom title to backend
      };

      // Send request to local server
      const response = await fetch('http://192.168.X.X:5555/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();
      
            if (result.status === 'success' || result.status === 'cancelled') {
              item.status = 'complete';
              item.completedAt = new Date().toISOString();
              processedCount++;
            } else {
              throw new Error(result.message || 'Processing failed');
            }
          } catch (error) {
            console.error('Error processing item:', error);
            item.status = 'failed';
            item.error = error.message;
            hasErrors = true;
          }
          
          // Save after each item is processed
          item.lastUpdated = new Date().toISOString();
          await saveQueueToStorage();
          updateQueueUI();
        } else if (item.status === 'complete') {
          processedCount++;
        }
      }
      
      // Show appropriate status message
      if (hasErrors) {
        showStatus(`Queue processing completed with errors. ${processedCount} items succeeded.`, 'error');
      } else if (processedCount > 0) {
        showStatus(`Queue processing complete! ${processedCount} items processed.`, 'success');
      } else {
        showStatus('No items were processed.', 'error');
      }
    } catch (error) {
      showStatus(`Error: ${error.message}`, 'error');
    } finally {
      processQueueButton.disabled = false;
    }
  });

  // Refresh queue button click handler
  refreshQueueButton.addEventListener('click', async function() {
    try {
      refreshQueueButton.textContent = "⟳";
      refreshQueueButton.disabled = true;
      
      // Reload queue from storage
      videoQueue = await getQueueFromStorage();
      
      // Check for items marked as processing but were abandoned
      const now = new Date().getTime();
      let updatedItems = 0;
      
      videoQueue.forEach(item => {
        // If item has been processing for more than 5 minutes, mark as failed
        if (item.status === 'processing') {
          const processingStartTime = new Date(item.lastUpdated || item.addedAt).getTime();
          if ((now - processingStartTime) > 5 * 60 * 1000) { // 5 minutes
            item.status = 'failed';
            item.error = 'Processing timed out';
            updatedItems++;
          }
        }
      });
      
      if (updatedItems > 0) {
        await saveQueueToStorage();
        showStatus(`Refreshed queue and recovered ${updatedItems} stuck item(s)`, 'success');
      } else {
        showStatus('Queue refreshed', 'success');
      }

      updateQueueUI();
    } catch (error) {
      showStatus(`Error refreshing queue: ${error.message}`, 'error');
    } finally {
      refreshQueueButton.textContent = "↻ Refresh";
      refreshQueueButton.disabled = false;
    }
  });
  
  // Clear all button click handler
  clearQueueButton.addEventListener('click', async function() {
    try {
      // Check if any items are currently processing
      const processingItems = videoQueue.filter(item => item.status === 'processing');
      if (processingItems.length > 0) {
        if (!confirm('Some items are still processing. Clear queue anyway?')) {
          return;
        }
      } else if (videoQueue.length === 0) {
        showStatus('Queue is already empty', 'error');
        return;
      } else if (!confirm('Are you sure you want to clear all items from the queue?')) {
        return;
      }
      
      // Clear queue
      videoQueue = [];
      await saveQueueToStorage();
      updateQueueUI();
      showStatus('Queue cleared', 'success');
    } catch (error) {
      showStatus(`Error clearing queue: ${error.message}`, 'error');
    }
  });

  // Update the queue UI
  function updateQueueUI() {
    queueListDiv.innerHTML = '';
    
    if (videoQueue.length === 0) {
      queueListDiv.innerHTML = '<p style="text-align: center; font-style: italic; color: #666;">No videos in queue</p>';
      processQueueButton.disabled = true;
      clearQueueButton.disabled = true;
      return;
    }
    
    // Count pending items
    const pendingCount = videoQueue.filter(item => item.status === 'pending' || item.status === 'failed').length;
    const processingCount = videoQueue.filter(item => item.status === 'processing').length;
    
    // Only enable button if there are pending items and no items currently processing
    processQueueButton.disabled = (pendingCount === 0);
    clearQueueButton.disabled = false;
    
    // Display status info
    const queueStatus = document.createElement('div');
    queueStatus.className = 'queue-status';
    queueStatus.style.marginBottom = '10px';
    queueStatus.style.fontSize = '12px';
    
    if (processingCount > 0) {
      queueStatus.innerHTML = `<strong>Status:</strong> Processing ${processingCount} item(s)...`;
      queueStatus.style.color = '#0d6efd';
    } else if (pendingCount > 0) {
      queueStatus.innerHTML = `<strong>Status:</strong> ${pendingCount} item(s) ready to process`;
      queueStatus.style.color = '#198754';
    } else {
      queueStatus.innerHTML = '<strong>Status:</strong> All items processed';
      queueStatus.style.color = '#198754';
    }
    
    queueListDiv.appendChild(queueStatus);
    
    // Sort queue items: processing first, then pending, then failed, then complete
    const sortedQueue = [...videoQueue].sort((a, b) => {
      const statusOrder = { 'processing': 0, 'pending': 1, 'failed': 2, 'complete': 3 };
      return statusOrder[a.status] - statusOrder[b.status] || 
             new Date(b.addedAt).getTime() - new Date(a.addedAt).getTime(); // Secondary sort by add date (newest first)
    });
    
    sortedQueue.forEach(item => {
      const queueItem = document.createElement('div');
      queueItem.className = 'queue-item';
      
      const titleSpan = document.createElement('span');
      titleSpan.textContent = item.title;
      titleSpan.style.overflow = 'hidden';
      titleSpan.style.textOverflow = 'ellipsis';
      titleSpan.style.whiteSpace = 'nowrap';
      titleSpan.style.maxWidth = '200px';
      
      if (item.error) {
        titleSpan.title = `Error: ${item.error}`;
        titleSpan.style.color = '#721c24';
      }
      
      const statusBadge = document.createElement('span');
      statusBadge.className = `status-badge ${item.status}`;
      statusBadge.textContent = item.status;
      
      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'queue-actions';
      
      // Only show remove button if not currently processing
      if (item.status !== 'processing') {
        const removeButton = document.createElement('button');
        removeButton.textContent = '✕';
        removeButton.style.padding = '1px 4px';
        removeButton.style.minWidth = 'auto';
        removeButton.style.fontSize = '11px';
        removeButton.style.backgroundColor = 'transparent';
        removeButton.style.color = '#dc3545';
        removeButton.addEventListener('click', (e) => {
          e.stopPropagation();
          removeQueueItem(item.id);
        });
        actionsDiv.appendChild(removeButton);
      }
      
      actionsDiv.insertBefore(statusBadge, actionsDiv.firstChild);
      
      queueItem.appendChild(titleSpan);
      queueItem.appendChild(actionsDiv);
      
      // Add click event to show item details
      queueItem.addEventListener('click', () => {
        showItemDetails(item);
      });
      
      queueListDiv.appendChild(queueItem);
    });
  }
  
  // Show item details
  function showItemDetails(item) {
    const details = [
      `<strong>Title:</strong> ${item.title}`,
      `<strong>Folder:</strong> ${item.folder}`,
      `<strong>Status:</strong> ${item.status}`,
      `<strong>Added:</strong> ${new Date(item.addedAt).toLocaleString()}`
    ];
    
    if (item.ticker_symbol) {
      details.push(`<strong>Ticker:</strong> ${item.ticker_symbol}`);
    }
    
    if (item.completedAt) {
      details.push(`<strong>Completed:</strong> ${new Date(item.completedAt).toLocaleString()}`);
    }
    
    if (item.error) {
      details.push(`<strong>Error:</strong> ${item.error}`);
    }
    
    showStatus(details.join('<br>'), item.status === 'failed' ? 'error' : 'success');
  }

  // Remove an item from the queue
  async function removeQueueItem(id) {
    try {
      const item = videoQueue.find(item => item.id === id);
      if (item && item.status === 'processing') {
        showStatus("Can't remove an item that's currently processing", 'error');
        return;
      }
      
      videoQueue = videoQueue.filter(item => item.id !== id);
      await saveQueueToStorage();
      updateQueueUI();
      showStatus('Item removed from queue', 'success');
    } catch (error) {
      console.error('Error removing item:', error);
      showStatus('Failed to remove item', 'error');
    }
  }

  // Save queue to chrome storage
  async function saveQueueToStorage() {
    return new Promise((resolve) => {
      try {
        // Check if chrome.storage is available
        if (!chrome || !chrome.storage || !chrome.storage.local) {
          console.error('Chrome storage API not available');
          resolve(); // Continue without storage
          return;
        }
        
        chrome.storage.local.set({ 'ytm4a_queue': videoQueue }, (result) => {
          if (chrome.runtime.lastError) {
            console.error('Error saving to storage:', chrome.runtime.lastError);
          }
          resolve(result);
        });
      } catch (error) {
        console.error('Error saving queue:', error);
        resolve(); // Continue without storage
      }
    });
  }

  // Get queue from chrome storage
  async function getQueueFromStorage() {
    return new Promise((resolve) => {
      try {
        // Check if chrome.storage is available
        if (!chrome || !chrome.storage || !chrome.storage.local) {
          console.error('Chrome storage API not available');
          resolve([]); // Return empty array
          return;
        }
        
        chrome.storage.local.get('ytm4a_queue', (result) => {
          if (chrome.runtime.lastError) {
            console.error('Error getting from storage:', chrome.runtime.lastError);
            resolve([]);
          } else {
            resolve(result.ytm4a_queue || []);
          }
        });
      } catch (error) {
        console.error('Error getting queue:', error);
        resolve([]); // Return empty array
      }
    });
  }

  // Show status message
  function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    statusDiv.style.display = 'block';
  }

  // Initial folder check
  folderSelect.dispatchEvent(new Event('change'));
}); 