var ChanLunCore = (function() {
    'use strict';

    function _isIncluded(a, b) {
        var aH = parseFloat(a.high), aL = parseFloat(a.low);
        var bH = parseFloat(b.high), bL = parseFloat(b.low);
        return (aH >= bH && aL <= bL) || (aH <= bH && aL >= bL);
    }

    function _deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    function mergeIncludedKLines(klines) {
        if (!klines || klines.length < 2) return _deepClone(klines);
        var merged = [];
        var trend = 0;
        var pending = _deepClone(klines[0]);
        pending._originalIndex = 0;

        for (var i = 1; i < klines.length; i++) {
            var curr = _deepClone(klines[i]);
            curr._originalIndex = i;

            if (_isIncluded(pending, curr)) {
                if (trend >= 0) {
                    pending.high = Math.max(parseFloat(pending.high), parseFloat(curr.high)).toFixed(2);
                    pending.low = Math.max(parseFloat(pending.low), parseFloat(curr.low)).toFixed(2);
                } else {
                    pending.high = Math.min(parseFloat(pending.high), parseFloat(curr.high)).toFixed(2);
                    pending.low = Math.min(parseFloat(pending.low), parseFloat(curr.low)).toFixed(2);
                }
            } else {
                var prevClose = parseFloat(pending.close);
                var currClose = parseFloat(curr.close);
                trend = currClose >= prevClose ? 1 : -1;
                merged.push(pending);
                pending = curr;
            }
        }
        merged.push(pending);
        return merged;
    }

    function detectFractals(mergedKlines) {
        var fractals = [];
        if (!mergedKlines || mergedKlines.length < 3) return fractals;
        for (var i = 1; i < mergedKlines.length - 1; i++) {
            var prev = mergedKlines[i - 1];
            var curr = mergedKlines[i];
            var next = mergedKlines[i + 1];
            var pH = parseFloat(prev.high), cH = parseFloat(curr.high), nH = parseFloat(next.high);
            var pL = parseFloat(prev.low), cL = parseFloat(curr.low), nL = parseFloat(next.low);

            if (cH > pH && cH > nH) {
                fractals.push({
                    type: 'top',
                    index: i,
                    originalIndex: curr._originalIndex !== undefined ? curr._originalIndex : i,
                    price: parseFloat(cH),
                    date: curr.trade_date,
                    lowPrice: parseFloat(cL)
                });
            }
            if (cL < pL && cL < nL) {
                fractals.push({
                    type: 'bottom',
                    index: i,
                    originalIndex: curr._originalIndex !== undefined ? curr._originalIndex : i,
                    price: parseFloat(cL),
                    date: curr.trade_date,
                    highPrice: parseFloat(cH)
                });
            }
        }
        return fractals;
    }

    function detectBis(fractals) {
        var bis = [];
        if (!fractals || fractals.length < 2) return bis;
        var lastFractal = null;

        for (var i = 0; i < fractals.length; i++) {
            var curr = fractals[i];

            if (lastFractal && lastFractal.type === curr.type) continue;

            if (lastFractal) {
                var gap = curr.originalIndex - lastFractal.originalIndex;
                if (gap < 1) continue;

                var direction = lastFractal.type === 'bottom' ? 'up' : 'down';
                bis.push({
                    start: { type: lastFractal.type, index: lastFractal.index, originalIndex: lastFractal.originalIndex, price: lastFractal.price, date: lastFractal.date },
                    end: { type: curr.type, index: curr.index, originalIndex: curr.originalIndex, price: curr.price, date: curr.date },
                    direction: direction,
                    startPrice: lastFractal.price,
                    endPrice: curr.price
                });
            }
            lastFractal = curr;
        }
        return bis;
    }

    function detectZhongshus(bis, options) {
        var opts = options || {};
        var minBiCount = opts.minBiCount || 3;
        var zhongshus = [];
        if (!bis || bis.length < minBiCount) return zhongshus;

        for (var i = 0; i <= bis.length - minBiCount; i++) {
            var window = bis.slice(i, i + minBiCount);
            var upHighs = [];
            var downLows = [];

            for (var j = 0; j < window.length; j++) {
                var b = window[j];
                var extreme = b.direction === 'up' ? Math.max(b.startPrice, b.endPrice) : Math.min(b.startPrice, b.endPrice);
                if (b.direction === 'up') upHighs.push(extreme); else downLows.push(extreme);
            }

            if (upHighs.length < 2 || downLows.length < 1) continue;

            var zg = Math.min.apply(null, upHighs);
            var zd = Math.max.apply(null, downLows);

            if (zg > zd) {
                var endIdx = i + minBiCount - 1;
                for (var k = i + minBiCount; k < bis.length; k++) {
                    var bk = bis[k];
                    var ek = bk.direction === 'up' ? Math.max(bk.startPrice, bk.endPrice) : Math.min(bk.startPrice, bk.endPrice);
                    if (ek >= zd && ek <= zg) { endIdx = k; } else break;
                }

                zhongshus.push({
                    zg: zg,
                    zd: zd,
                    startBiIndex: i,
                    endBiIndex: endIdx,
                    biCount: endIdx - i + 1,
                    startDate: bis[i].start.date,
                    endDate: bis[endIdx].end.date
                });
                i = endIdx;
            }
        }
        return zhongshus;
    }

    function detectXianduans(bis, options) {
        var opts = options || {};
        var minBiForXd = opts.minBiForXd || 3;
        var xianduans = [];
        if (!bis || bis.length < minBiForXd) return xianduans;

        var i = 0;
        while (i < bis.length) {
            var segStart = i;
            var segDir = bis[i].direction;
            var candidateBis = [bis[i]];
            var j = i + 1;
            var broken = false;

            while (j < bis.length && candidateBis.length < minBiForXd) {
                candidateBis.push(bis[j]);
                j++;
            }

            if (candidateBis.length >= minBiForXd) {
                var firstEndPrice = candidateBis[0].endPrice;
                var lastEndPrice = candidateBis[candidateBis.length - 1].endPrice;
                var xdDir = lastEndPrice > firstEndPrice ? 'up' : 'down';
                var breakPoint = xdDir === 'up'
                    ? Math.min(candidateBis[0].startPrice, candidateBis[0].endPrice)
                    : Math.max(candidateBis[0].startPrice, candidateBis[0].endPrice);

                while (j < bis.length) {
                    var nextBi = bis[j];
                    var nextExtreme = xdDir === 'up' ? Math.min(nextBi.startPrice, nextBi.endPrice) : Math.max(nextBi.startPrice, nextBi.endPrice);
                    if ((xdDir === 'up' && nextExtreme < breakPoint) || (xdDir === 'down' && nextExtreme > breakPoint)) {
                        broken = true;
                        break;
                    }
                    candidateBis.push(nextBi);
                    j++;
                }

                var xdStart = candidateBis[0].start;
                var xdEnd = candidateBis[candidateBis.length - 1].end;
                xianduans.push({
                    start: { type: xdStart.type, index: xdStart.index, originalIndex: xdStart.originalIndex, price: xdStart.price, date: xdStart.date },
                    end: { type: xdEnd.type, index: xdEnd.index, originalIndex: xdEnd.originalIndex, price: xdEnd.price, date: xdEnd.date },
                    direction: xdDir,
                    startPrice: xdStart.price,
                    endPrice: xdEnd.price,
                    biCount: candidateBis.length,
                    biIndices: candidateBis.map(function(b, idx) { return segStart + idx; })
                });
                i = broken ? j : j;
            } else {
                i++;
            }
        }

        var merged = [];
        for (var m = 0; m < xianduans.length; m++) {
            var cur = xianduans[m];
            if (merged.length > 0 && merged[merged.length - 1].direction === cur.direction) {
                var last = merged[merged.length - 1];
                last.end = cur.end;
                last.endPrice = cur.endPrice;
                last.biCount += cur.biCount;
                if (cur.biIndices) {
                    last.biIndices = last.biIndices.concat(cur.biIndices);
                }
            } else {
                merged.push(JSON.parse(JSON.stringify(cur)));
            }
        }
        console.log('[ChanLunCore] 线段合并前: ' + xianduans.length + ' 条 → 合并后: ' + merged.length + ' 条');
        return merged;
    }

    function analyze(klines, options) {
        if (!klines || klines.length < 5) {
            return { mergedKlines: [], fractals: [], bis: [], zhongshus: [], xianduans: [], stats: { fractalCount: 0, biCount: 0, zhongshuCount: 0, xianduanCount: 0 } };
        }
        var sorted = klines.slice().sort(function(a, b) { return a.trade_date.localeCompare(b.trade_date); });
        var merged = mergeIncludedKLines(sorted);
        console.log('[ChanLunCore] 包含处理后K线数: ' + merged.length + ' (原始: ' + sorted.length + ')');

        var fractals = detectFractals(merged);
        console.log('[ChanLunCore] 检测到分型: ' + fractals.length + ' 个');
        fractals.forEach(function(f, i) {
            console.log('  分型#' + i + ': ' + f.type.toUpperCase() + ' @ ' + f.date + ' price=' + f.price.toFixed(2));
        });

        var bis = detectBis(fractals);
        console.log('[ChanLunCore] 检测到笔: ' + bis.length + ' 条');
        bis.forEach(function(b, i) {
            console.log('  笔#' + (i+1) + '(' + b.direction.toUpperCase() + '): ' + b.start.date + '[' + b.startPrice.toFixed(2) + '] → ' + b.end.date + '[' + b.endPrice.toFixed(2) + ']');
        });

        var zhongshus = detectZhongshus(bis, options);
        console.log('[ChanLunCore] 检测到中枢: ' + zhongshus.length + ' 个');
        zhongshus.forEach(function(z, i) {
            console.log('  中枢#' + (i+1) + ': ZG=' + z.zg.toFixed(2) + ' ZD=' + z.zd.toFixed(2) + ' [' + z.startDate + ' ~ ' + z.endDate + '] ' + z.biCount + '笔');
        });

        var xianduans = detectXianduans(bis, options);
        console.log('[ChanLunCore] 检测到线段: ' + xianduans.length + ' 条');
        xianduans.forEach(function(x, i) {
            console.log('  线段#' + (i+1) + '(' + x.direction.toUpperCase() + '): ' + x.start.date + '[' + x.startPrice.toFixed(2) + '] → ' + x.end.date + '[' + x.endPrice.toFixed(2) + '] (' + x.biCount + '笔)');
        });

        return {
            mergedKlines: merged,
            fractals: fractals,
            bis: bis,
            zhongshus: zhongshus,
            xianduans: xianduans,
            stats: {
                fractalCount: fractals.length,
                biCount: bis.length,
                zhongshuCount: zhongshus.length,
                xianduanCount: xianduans.length
            }
        };
    }

    return {
        mergeIncludedKLines: mergeIncludedKLines,
        detectFractals: detectFractals,
        detectBis: detectBis,
        detectZhongshus: detectZhongshus,
        detectXianduans: detectXianduans,
        analyze: analyze
    };
})();

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChanLunCore;
}
