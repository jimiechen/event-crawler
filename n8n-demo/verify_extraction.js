const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');

async function searchBaidu(keyword = '小米汽车') {
    try {
        const url = `https://www.baidu.com/s?wd=${encodeURIComponent(keyword)}`;
        const headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        };
        
        console.log(`Fetching ${url}...`);
        const response = await axios.get(url, { headers });
        const html = response.data;
        const $ = cheerio.load(html);
        
        const titles = [];
        
        $('.c-container').each((i, el) => {
            // Try to find the title element
            // Common selectors for Baidu: h3.t > a, or just h3 > a
            let titleEl = $(el).find('h3').first();
            if (titleEl.length === 0) {
                 titleEl = $(el).find('.c-title').first();
            }

            const title = titleEl.text().trim();
            
            if (title) {
                titles.push(title);
            }
        });
        
        const top3 = titles.slice(0, 3);
        console.log('Found top 3 titles:', JSON.stringify(top3, null, 2));

        const output = {
            keyword: keyword,
            titles: top3,
            count: top3.length,
            timestamp: new Date().toISOString()
        };

        const outputPath = path.join(__dirname, 'search_results.json');
        fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
        console.log(`Saved results to ${outputPath}`);
        
    } catch (error) {
        console.error('Error:', error.message);
        // Write error to file so UI can see it
         const outputPath = path.join(__dirname, 'search_results.json');
         fs.writeFileSync(outputPath, JSON.stringify({ error: error.message }, null, 2));
    }
}

// Get keyword from command line args if present
const keywordArg = process.argv[2];
searchBaidu(keywordArg || '小米汽车');
