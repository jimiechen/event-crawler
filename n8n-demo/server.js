const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 5173;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Redirect root to the pro editor
app.get('/', (req, res) => {
    res.redirect('/pro/');
});

// Explicit route for /pro/ to serve the index.html
app.get(/\/pro\/.*/, (req, res) => {
    res.sendFile(path.join(__dirname, 'public/pro/index.html'));
});
app.get('/pro', (req, res) => {
    res.sendFile(path.join(__dirname, 'public/pro/index.html'));
});

// Path to workflow file and results
const WORKFLOW_PATH = path.join(__dirname, 'baidu_search_workflow.json');
const RESULTS_PATH = path.join(__dirname, 'search_results.json');
const SCRIPT_PATH = path.join(__dirname, 'verify_extraction.js');

// Get Workflow JSON
app.get('/api/workflow', (req, res) => {
    try {
        if (fs.existsSync(WORKFLOW_PATH)) {
            const data = fs.readFileSync(WORKFLOW_PATH, 'utf8');
            res.json(JSON.parse(data));
        } else {
            res.status(404).json({ error: 'Workflow file not found' });
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Update Workflow (Simulated editing)
app.post('/api/workflow', (req, res) => {
    try {
        const { keyword } = req.body;
        if (!keyword) {
            return res.status(400).json({ error: 'Keyword is required' });
        }

        // Update the JSON file to reflect the change (simulating n8n editor)
        if (fs.existsSync(WORKFLOW_PATH)) {
            const workflow = JSON.parse(fs.readFileSync(WORKFLOW_PATH, 'utf8'));
            
            // Find the HTTP Request node and update the URL
            const httpNode = workflow.nodes.find(n => n.type === 'n8n-nodes-base.httpRequest');
            if (httpNode) {
                httpNode.parameters.url = `https://www.baidu.com/s?wd=${encodeURIComponent(keyword)}`;
            }

            fs.writeFileSync(WORKFLOW_PATH, JSON.stringify(workflow, null, 2));
        }

        res.json({ success: true, message: 'Workflow updated' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Execute Workflow
app.post('/api/run', (req, res) => {
    const { keyword } = req.body;
    const searchTerm = keyword || '小米汽车';

    console.log(`Executing workflow with keyword: ${searchTerm}`);

    exec(`node verify_extraction.js "${searchTerm}"`, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            return res.status(500).json({ error: error.message, details: stderr });
        }
        
        console.log(`stdout: ${stdout}`);
        
        // Read the results file
        try {
            if (fs.existsSync(RESULTS_PATH)) {
                const results = JSON.parse(fs.readFileSync(RESULTS_PATH, 'utf8'));
                res.json({ success: true, results });
            } else {
                res.json({ success: false, error: 'No results file generated' });
            }
        } catch (readErr) {
            res.status(500).json({ error: 'Failed to read results', details: readErr.message });
        }
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Workflow Dashboard running at http://localhost:${PORT}`);
});
