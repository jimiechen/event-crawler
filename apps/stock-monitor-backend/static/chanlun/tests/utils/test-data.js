var ChanLunTestUtils = (function() {
    'use strict';

    function addDays(dateStr, days) {
        var d = new Date(dateStr.substring(0, 4) + '-' + dateStr.substring(4, 6) + '-' + dateStr.substring(6, 8));
        d.setDate(d.getDate() + days);
        var m = (d.getMonth() + 1).toString().padStart(2, '0');
        var day = d.getDate().toString().padStart(2, '0');
        return d.getFullYear().toString() + m + day;
    }

    function generateTestKData(patterns, baseDate) {
        var date = baseDate || '20250101';
        return patterns.map(function(p, i) {
            return {
                trade_date: addDays(date, i),
                open: p.open !== undefined ? p.open.toFixed(2) : (p.low + Math.random() * (p.high - p.low)).toFixed(2),
                high: p.high.toFixed(2),
                low: p.low.toFixed(2),
                close: p.close.toFixed(2),
                volume: p.volume || Math.floor(Math.random() * 1000000) + 100000
            };
        });
    }

    function generateRandomKData(count) {
        var price = 10;
        var result = [];
        for (var i = 0; i < count; i++) {
            var change = (Math.random() - 0.48) * 0.5;
            price = price * (1 + change);
            var high = price * (1 + Math.random() * 0.03);
            var low = price * (1 - Math.random() * 0.03);
            var open_ = low + Math.random() * (high - low);
            var close = low + Math.random() * (high - low);
            result.push({
                trade_date: addDays('20240101', i),
                open: open_.toFixed(2), high: high.toFixed(2),
                low: low.toFixed(2), close: close.toFixed(2),
                volume: Math.floor(Math.random() * 2000000) + 500000
            });
        }
        return result;
    }

    function generateTrend(count, startPrice, endPrice, direction) {
        var result = [];
        var step = (endPrice - startPrice) / count;
        for (var i = 0; i < count; i++) {
            var base = startPrice + step * i;
            var volatility = (Math.random() - 0.5) * Math.abs(step) * 1.5;
            var p = base + volatility;
            var h = p + Math.abs(volatility) * (0.5 + Math.random());
            var l = p - Math.abs(volatility) * (0.5 + Math.random());
            var o = l + Math.random() * (h - l);
            var c = l + Math.random() * (h - l);
            if (direction === 'down') { c = o - Math.abs(c - o); }
            else { c = o + Math.abs(c - o); }
            result.push({ high: h, low: l, open: o, close: c });
        }
        return result;
    }

    function generateRisingFallingPattern() {
        return []
            .concat(generateTrend(10, 10, 15, 'up'))
            .concat(generateTrend(10, 15, 11, 'down'))
            .concat(generateTrend(10, 11, 18, 'up'))
            .concat(generateTrend(10, 18, 13, 'down'))
            .concat(generateTrend(20, 13, 16, 'flat'));
    }

    function generateZhongshuPattern() {
        return []
            .concat(generateTrend(5, 10, 16, 'up'))
            .concat(generateTrend(5, 16, 13, 'down'))
            .concat(generateTrend(8, 13, 15.5, 'up'))
            .concat(generateTrend(8, 15.5, 12.5, 'down'))
            .concat(generateTrend(8, 12.5, 15, 'up'))
            .concat(generateTrend(8, 15, 12, 'down'))
            .concat(generateTrend(5, 12, 19, 'up'));
    }

    return {
        generateTestKData: generateTestKData,
        generateRandomKData: generateRandomKData,
        generateRisingFallingPattern: generateRisingFallingPattern,
        generateZhongshuPattern: generateZhongshuPattern
    };
})();
