(function() {
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
                transition: opacity 0.3s ease, visibility 0.3s ease;
            }
            .custom-alert-overlay.show {
                opacity: 1;
                visibility: visible;
            }
            .custom-alert-box {
                background: white;
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                max-width: 400px;
                width: 90%;
                text-align: center;
                transform: scale(0.9);
                transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
                font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            }
            .custom-alert-overlay.show .custom-alert-box {
                transform: scale(1);
            }
            .custom-alert-message {
                margin-bottom: 24px;
                font-size: 16px;
                color: #1f2937;
                line-height: 1.6;
                word-wrap: break-word;
            }
            .custom-alert-btn {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: background-color 0.2s;
                outline: none;
            }
            .custom-alert-btn:hover {
                background-color: #2563eb;
            }
            .custom-alert-btn:active {
                background-color: #1d4ed8;
            }
        `;
        document.head.appendChild(style);

        const overlay = document.createElement('div');
        overlay.className = 'custom-alert-overlay';
        
        const box = document.createElement('div');
        box.className = 'custom-alert-box';
        
        const messageEl = document.createElement('div');
        messageEl.className = 'custom-alert-message';
        
        const btn = document.createElement('button');
        btn.className = 'custom-alert-btn';
        btn.textContent = '确定';
        
        box.appendChild(messageEl);
        box.appendChild(btn);
        overlay.appendChild(box);
        document.body.appendChild(overlay);

        function closeAlert() {
            overlay.classList.remove('show');
        }
        
        btn.addEventListener('click', closeAlert);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeAlert();
        });

        // Override window.alert
        window.alert = function(message) {
             if (typeof message === 'object') {
                try {
                    message = JSON.stringify(message, null, 2);
                } catch (e) {}
            }
            messageEl.textContent = String(message);
            overlay.classList.add('show');
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCustomAlert);
    } else {
        initCustomAlert();
    }
})();
