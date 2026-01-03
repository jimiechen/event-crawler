(function() {
    // Prevent duplicate initialization
    if (window._customAlertInitialized) return;
    window._customAlertInitialized = true;

    // Queue for alerts
    const alertQueue = [];
    let isAlertShowing = false;

    function initCustomAlert() {
        if (document.getElementById('custom-alert-style')) return;

        const style = document.createElement('style');
        style.id = 'custom-alert-style';
        style.textContent = `
            .custom-alert-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 99999;
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.2s ease, visibility 0.2s ease;
                backdrop-filter: blur(2px);
            }
            .custom-alert-overlay.show {
                opacity: 1;
                visibility: visible;
            }
            .custom-alert-box {
                background: white;
                padding: 24px 32px;
                border-radius: 12px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                max-width: 450px;
                width: 90%;
                text-align: center;
                transform: scale(0.95);
                transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
                font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            .custom-alert-overlay.show .custom-alert-box {
                transform: scale(1);
            }
            .custom-alert-icon {
                width: 48px;
                height: 48px;
                margin-bottom: 16px;
                color: #3b82f6;
            }
            .custom-alert-title {
                font-size: 18px;
                font-weight: 600;
                color: #111827;
                margin-bottom: 8px;
            }
            .custom-alert-message {
                margin-bottom: 24px;
                font-size: 15px;
                color: #4b5563;
                line-height: 1.6;
                word-wrap: break-word;
                max-height: 60vh;
                overflow-y: auto;
                width: 100%;
            }
            .custom-alert-btn {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 32px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.2s;
                outline: none;
                box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.5);
            }
            .custom-alert-btn:hover {
                background-color: #2563eb;
                box-shadow: 0 6px 8px -1px rgba(59, 130, 246, 0.6);
                transform: translateY(-1px);
            }
            .custom-alert-btn:active {
                background-color: #1d4ed8;
                transform: translateY(0);
            }
        `;
        document.head.appendChild(style);

        const overlay = document.createElement('div');
        overlay.className = 'custom-alert-overlay';
        
        const box = document.createElement('div');
        box.className = 'custom-alert-box';
        
        // Icon (Info circle)
        box.innerHTML = `
            <svg class="custom-alert-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="custom-alert-title">提示</div>
            <div class="custom-alert-message"></div>
            <button class="custom-alert-btn">我知道了</button>
        `;
        
        const messageEl = box.querySelector('.custom-alert-message');
        const btn = box.querySelector('.custom-alert-btn');
        
        overlay.appendChild(box);
        document.body.appendChild(overlay);

        function showNextAlert() {
            if (alertQueue.length === 0) {
                isAlertShowing = false;
                overlay.classList.remove('show');
                // Allow interaction with background
                setTimeout(() => {
                    if (!isAlertShowing) overlay.style.visibility = 'hidden';
                }, 200); 
                return;
            }

            isAlertShowing = true;
            const message = alertQueue.shift();
            
            // Handle Object/Array display
            let displayMsg = message;
            if (typeof message === 'object') {
                try {
                    displayMsg = JSON.stringify(message, null, 2);
                    messageEl.style.textAlign = 'left';
                    messageEl.style.whiteSpace = 'pre-wrap';
                    messageEl.style.fontFamily = 'monospace';
                    messageEl.style.fontSize = '13px';
                    messageEl.style.backgroundColor = '#f3f4f6';
                    messageEl.style.padding = '12px';
                    messageEl.style.borderRadius = '6px';
                } catch (e) {
                    displayMsg = String(message);
                }
            } else {
                messageEl.style.textAlign = 'center';
                messageEl.style.whiteSpace = 'normal';
                messageEl.style.fontFamily = 'inherit';
                messageEl.style.fontSize = '15px';
                messageEl.style.backgroundColor = 'transparent';
                messageEl.style.padding = '0';
            }

            messageEl.textContent = displayMsg;
            overlay.style.visibility = 'visible'; // Ensure visible before opacity transition
            // Force reflow
            void overlay.offsetWidth;
            overlay.classList.add('show');
        }

        function closeAlert() {
            overlay.classList.remove('show');
            setTimeout(showNextAlert, 200); // Wait for transition
        }
        
        btn.addEventListener('click', closeAlert);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeAlert();
        });
        
        // Handle Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isAlertShowing) {
                closeAlert();
            }
        });

        // Override window.alert
        window.alert = function(message) {
            alertQueue.push(message);
            if (!isAlertShowing) {
                showNextAlert();
            }
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCustomAlert);
    } else {
        initCustomAlert();
    }
})();
