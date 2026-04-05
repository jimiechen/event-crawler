var ChanLunKline = (function() {
    'use strict';

    var RC = window.Recharts;
    if (!RC) { console.error('[ChanLunKline] Recharts 未加载!'); return null; }

    var ComposedChart = RC.ComposedChart, XAxis = RC.XAxis, YAxis = RC.YAxis;
    var Tooltip = RC.Tooltip, Legend = RC.Legend, Bar = RC.Bar, Line = RC.Line;
    var ResponsiveContainer = RC.ResponsiveContainer;
    var Brush = RC.Brush, CartesianGrid = RC.CartesianGrid;

    function calcMA(data, period) {
        var result = [];
        for (var i = 0; i < data.length; i++) {
            if (i < period - 1) { result.push(null); continue; }
            var sum = 0;
            for (var j = 0; j < period; j++) { sum += parseFloat(data[i - j].close); }
            result.push(+(sum / period).toFixed(4));
        }
        return result;
    }

    function calcEXPMA(data, period) {
        var result = [];
        var k = 2 / (period + 1);
        for (var i = 0; i < data.length; i++) {
            if (i === 0) { result.push(parseFloat(data[i].close)); continue; }
            result.push(+((parseFloat(data[i].close) * k + result[i - 1] * (1 - k)).toFixed(4)));
        }
        return result;
    }

    function prepareChartData(dailyData) {
        var sorted = dailyData.slice().sort(function(a, b) { return a.trade_date.localeCompare(b.trade_date); });
        var ma5 = calcMA(sorted, 5), ma10 = calcMA(sorted, 10);
        var ma20 = calcMA(sorted, 20), ma60 = calcMA(sorted, 60);
        var expma13 = calcEXPMA(sorted, 13);

        return sorted.map(function(item, idx) {
            return Object.assign({}, item, {
                _ma5: ma5[idx], _ma10: ma10[idx], _ma20: ma20[idx], _ma60: ma60[idx],
                _expma13: expma13[idx],
                ohlc: {
                    o: +(parseFloat(item.open).toFixed(2)),
                    h: +(parseFloat(item.high).toFixed(2)),
                    l: +(parseFloat(item.low).toFixed(2)),
                    c: +(parseFloat(item.close).toFixed(2))
                },
                _idx: idx
            });
        });
    }

    function CandlestickShape(props) {
        var x = props.x, y = props.y, width = props.width, height = props.height, payload = props.payload;
        if (!payload || !payload.ohlc) return null;
        var o = payload.ohlc.o, h = payload.ohlc.h, l = payload.ohlc.l, c = payload.ohlc.c;
        var yMin = props.yDomain[0], yMax = props.yDomain[1];
        var yRange = yMax - yMin || 1;

        // 调试日志：打印前2根蜡烛
        if (payload._idx < 2) {
            console.log('[CandlestickShape] idx=' + payload._idx + ' OHLC={' + o + ',' + h + ',' + l + ',' + c + '} ' +
                        'yDomain=[' + yMin.toFixed(2) + ',' + yMax.toFixed(2) + '] props.y=' + y.toFixed(1) + ' height=' + height.toFixed(1));
        }

        var isUp = c >= o;
        var color = isUp ? '#ec0000' : '#00da3c';
        var borderColor = isUp ? '#8A0000' : '#008F28';

        // 关键：Bar的props.y是该Bar的底部Y坐标（对应close价格）
        // height是Bar的高度（从close到0）
        // 我们需要基于yDomain重新计算每个价格相对于这个Bar的位置
        var barBottomPrice = yMin;  // Bar底部对应的价格
        var barTopPrice = yMax;     // Bar顶部对应的价格
        
        function priceToPixel(price) {
            // 将价格映射到当前Bar的局部坐标系
            // y是Bar的底部（SVG坐标），height是Bar高度
            // 但Bar的高度是基于dataKey(close)计算的，不是基于yDomain
            // 所以我们需要基于yDomain重新计算
            var ratio = (price - yMin) / yRange;
            // props.y是close价格对应的SVG坐标
            // 我们需要找出close价格在yDomain中的比例位置
            var closeRatio = (c - yMin) / yRange;
            var closePixelY = y + height - (closeRatio * height); // close在SVG中的位置
            
            // 其他价格相对于close的偏移
            var priceOffset = (price - c) / yRange * height;
            return closePixelY - priceOffset;
        }

        var yTop = priceToPixel(Math.max(o, c));
        var yBot = priceToPixel(Math.min(o, c));
        var yHigh = priceToPixel(h);
        var yLow = priceToPixel(l);
        var cx = x + width / 2;
        var bw = Math.max(width * 0.65, 2);

        return React.createElement('g', null,
            React.createElement('line', { x1: cx, y1: yHigh, x2: cx, y2: yTop, stroke: color, strokeWidth: 1 }),
            React.createElement('line', { x1: cx, y1: yBot, x2: cx, y2: yLow, stroke: color, strokeWidth: 1 }),
            React.createElement('rect', { x: cx - bw / 2, y: yTop, width: bw, height: Math.max(yBot - yTop, 1), fill: color, stroke: borderColor, strokeWidth: 1 })
        );
    }

    function VolumeBarShape(props) {
        var x = props.x, y = props.y, width = props.width, height = props.height, payload = props.payload;
        if (!payload) return null;
        var vol = parseFloat(payload.volume || payload.vol || 0);
        var isUp = parseFloat(payload.close) >= parseFloat(payload.open);
        var color = isUp ? '#ec0000' : '#00da3c';
        var maxVol = props.maxVol || vol;
        var barH = maxVol > 0 ? (vol / maxVol) * height : height;
        return React.createElement('rect', { x: x, y: y + height - barH, width: width, height: Math.max(barH, 1), fill: color, opacity: 0.7 });
    }

    function CustomTooltip(props) {
        if (!props.active || !props.payload || !props.payload.length) return null;
        var p = props.payload[0].payload;
        if (!p) return null;
        var isUp = p.ohlc && p.ohlc.c >= p.ohlc.o;
        var upColor = isUp ? '#dc2626' : '#16a34a';
        var dnColor = isUp ? '#16a34a' : '#dc2626';
        var volVal = parseFloat(p.volume || 0);
        var volStr = volVal >= 10000 ? (volVal / 10000).toFixed(1) + ' 万手' : volVal.toFixed(0) + ' 手';
        return React.createElement('div', { style: { background: 'rgba(255,255,255,0.97)', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 16px', fontSize: 12.5, boxShadow: '0 4px 16px rgba(0,0,0,0.15)', lineHeight: 1.7, fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif', minWidth: 220 } },
            React.createElement('div', { style: { fontWeight: 700, color: '#1e293b', marginBottom: 6, fontSize: 13 } }, '\uD83D\uDCC5 ' + p.trade_date),
            React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'auto auto', gap: '4px 16px' } },
                React.createElement('span', { style: { color: '#94a3b8' } }, '\u5F00\u76D8'),
                React.createElement('span', { style: { color: upColor, fontWeight: 600, fontVariantNumeric: 'tabular-nums' } }, parseFloat(p.open).toFixed(2)),
                React.createElement('span', { style: { color: '#94a3b8' } }, '\u6700\u9AD8'),
                React.createElement('span', { style: { color: '#ef4444', fontWeight: 600, fontVariantNumeric: 'tabular-nums' } }, parseFloat(p.high).toFixed(2)),
                React.createElement('span', { style: { color: '#94a3b8' } }, '\u6700\u4F4E'),
                React.createElement('span', { style: { color: '#22c55e', fontWeight: 600, fontVariantNumeric: 'tabular-nums' } }, parseFloat(p.low).toFixed(2)),
                React.createElement('span', { style: { color: '#94a3b8' } }, '\u6536\u76D8'),
                React.createElement('span', { style: { color: upColor, fontWeight: 600, fontVariantNumeric: 'tabular-nums' } }, parseFloat(p.close).toFixed(2))
            ),
            React.createElement('div', { style: { marginTop: 6, paddingTop: 6, borderTop: '1px solid #f1f5f9', color: '#6366f1', fontSize: 11.5 } },
                '\uD83D\uDCCA \u6210\u91CF: ', React.createElement('span', { style: { fontWeight: 600, fontVariantNumeric: 'tabular-nums' } }, volStr))
        );
    }

    function ChanOverlay(props) {
        var biData = props.biData || [], zhongshuData = props.zhongshuData || [], xianduanData = props.xianduanData || [];
        var showBi = props.showBi !== false, showZhongshu = props.showZhongshu !== false;
        var showXianduan = props.showXianduan !== false, showLabel = props.showLabel !== false;
        var dates = props.dates || [];
        var plotArea = props.plotArea || {};
        var pw = plotArea.width || 800, ph = plotArea.height || 400;
        var pl = plotArea.left || 0, pt = plotArea.top || 0;
        var yMin = props.yMin, yMax = props.yMax;
        var yRange = yMax - yMin || 1;
        var brushRange = props.brushRange || {};
        var brushStart = brushRange.start || 0, brushEnd = brushRange.end || (dates.length - 1);

        if ((!showBi && !showZhongshu && !showXianduan && !showLabel)) return null;
        if (!dates.length) return null;

        var visibleCount = brushEnd - brushStart + 1;
        function mapX(dateIdx) {
            if (dateIdx < brushStart || dateIdx > brushEnd) return -9999;
            return pl + ((dateIdx - brushStart) / (visibleCount - 1 || 1)) * pw;
        }
        function mapY(priceVal) { return pt + ph - ((priceVal - yMin) / yRange) * ph; }

        var elements = [];

        if (showZhongshu && zhongshuData.length > 0) {
            zhongshuData.forEach(function(zs, zi) {
                var si = dates.indexOf(zs.startDate), ei = dates.indexOf(zs.endDate);
                if (si === -1 || ei === -1) return;
                var x1 = mapX(si), x2 = mapX(ei);
                if (x1 < -9990 || x2 < -9990) return;
                var yg = mapY(zs.zg), yd = mapY(zs.zd);
                var zsH = Math.max(yd - yg, 3);
                var zsAmp = zs.zg - zs.zd;
                var isSmallZhongshu = zsAmp < 1.0;
                var zsStyle = isSmallZhongshu ? {
                    fill: 'rgba(139,92,246,0.06)', stroke: '#a855f7', strokeDasharray: '4,3'
                } : {
                    fill: 'rgba(103,232,249,0.12)', stroke: '#22d3ee', strokeDasharray: '4,4'
                };
                elements.push(
                    React.createElement('rect', { key: 'zs-bg-' + zi,
                        x: Math.min(x1, x2), y: yg, width: Math.abs(x2 - x1) || 2, height: zsH,
                        fill: zsStyle.fill, stroke: zsStyle.stroke,
                        strokeWidth: 0.8, strokeDasharray: zsStyle.strokeDasharray, rx: 2
                    })
                );
            });
        }

        if (showBi && biData.length > 0) {
            biData.forEach(function(bi, biIdx) {
                var si = dates.indexOf(bi.start.date), ei = dates.indexOf(bi.end.date);
                if (si === -1 || ei === -1) return;
                var x1 = mapX(si), x2 = mapX(ei);
                if (x1 < -9990 || x2 < -9990) return;
                elements.push(
                    React.createElement('line', { key: 'bi-line-' + biIdx,
                        x1: x1, y1: mapY(bi.startPrice), x2: x2, y2: mapY(bi.endPrice),
                        stroke: '#dc2626', strokeWidth: 1.5, opacity: 0.85, strokeLinecap: 'round'
                    })
                );
                elements.push(
                    React.createElement('circle', { key: 'bi-dot-e-' + biIdx,
                        cx: x2, cy: mapY(bi.endPrice), r: 2.5,
                        fill: bi.end.type === 'top' ? '#ef4444' : '#22c55e',
                        stroke: '#fff', strokeWidth: 0.5
                    })
                );
            });
        }

        if (showBi && biData.length >= 3) {
            var beichiBi = biData[2];
            if (beichiBi && beichiBi.end.type === 'top') {
                var bci = dates.indexOf(beichiBi.end.date);
                if (bci !== -1) {
                    var bcPx = mapX(bci), bcPy = mapY(beichiBi.endPrice);
                    if (bcPx > -9990) {
                        elements.push(React.createElement('circle', { key: 'beichi-bg',
                            cx: bcPx, cy: bcPy, r: 9,
                            fill: 'none', stroke: '#16a34a', strokeWidth: 2, opacity: 0.85
                        }));
                        elements.push(React.createElement('text', { key: 'beichi-tx',
                            x: bcPx, y: bcPy + 4, textAnchor: 'middle',
                            fill: '#16a34a', fontSize: 15, fontWeight: 'bold', fontFamily: 'Arial,sans-serif'
                        }, '\u00D8'));
                    }
                }
            }
        }

        if (showXianduan && xianduanData.length > 0) {
            xianduanData.forEach(function(xd, xdIdx) {
                var si = dates.indexOf(xd.start.date), ei = dates.indexOf(xd.end.date);
                if (si === -1 || ei === -1) return;
                var x1 = mapX(si), x2 = mapX(ei);
                if (x1 < -9990 || x2 < -9990) return;
                var xdColor = '#3b82f6';
                elements.push(
                    React.createElement('line', { key: 'xd-line-' + xdIdx,
                        x1: x1, y1: mapY(xd.startPrice), x2: x2, y2: mapY(xd.endPrice),
                        stroke: xdColor, strokeWidth: 3.5, opacity: 0.88, strokeLinecap: 'round'
                    })
                );
                elements.push(
                    React.createElement('circle', { key: 'xd-dot-s-' + xdIdx,
                        cx: x1, cy: mapY(xd.startPrice), r: 4,
                        fill: '#3b82f6',
                        stroke: '#fff', strokeWidth: 1
                    })
                );
                elements.push(
                    React.createElement('circle', { key: 'xd-dot-e-' + xdIdx,
                        cx: x2, cy: mapY(xd.endPrice), r: 4.5,
                        fill: '#3b82f6',
                        stroke: '#fff', strokeWidth: 1
                    })
                );
            });
        }

        if (showLabel && biData.length > 0) {
            var peaks = [];
            for (var i = 0; i < biData.length; i++) {
                var b = biData[i];
                var di = dates.indexOf(b.end.date);
                if (di === -1 || di < brushStart || di > brushEnd) continue;
                var isPeak = true;
                if (b.end.type === 'top') {
                    var prevTop = null, nextTop = null;
                    for (var j = i - 1; j >= 0 && prevTop === null; j--) { if (biData[j].end.type === 'top') prevTop = biData[j].endPrice; }
                    for (var k = i + 1; k < biData.length && nextTop === null; k++) { if (biData[k].end.type === 'top') nextTop = biData[k].endPrice; }
                    if ((prevTop !== null && b.endPrice <= prevTop) || (nextTop !== null && b.endPrice <= nextTop)) isPeak = false;
                } else {
                    var prevBot = null, nextBot = null;
                    for (var j2 = i - 1; j2 >= 0 && prevBot === null; j2--) { if (biData[j2].end.type === 'bottom') prevBot = biData[j2].endPrice; }
                    for (var k2 = i + 1; k2 < biData.length && nextBot === null; k2++) { if (biData[k2].end.type === 'bottom') nextBot = biData[k2].endPrice; }
                    if ((prevBot !== null && b.endPrice >= prevBot) || (nextBot !== null && b.endPrice >= nextBot)) isPeak = false;
                }
                if (isPeak) peaks.push({ dateIndex: di, price: b.endPrice, type: b.end.type });
            }
            var maxLabels = 15;
            if (peaks.length > maxLabels) {
                var step = Math.ceil(peaks.length / maxLabels);
                peaks = peaks.filter(function(_, idx) { return idx % step === 0; });
            }
            peaks.forEach(function(pt, li) {
                var px = mapX(pt.dateIndex);
                if (px < -9990) return;
                var py = mapY(pt.price);
                var txt = pt.price.toFixed(2);
                var clr = pt.type === 'top' ? '#dc2626' : '#16a34a';
                var offsetY = pt.type === 'top' ? -7 : 15;
                elements.push(React.createElement('text', { key: 'lbl-bg-' + li, x: px + 4, y: py + offsetY,
                    fill: clr, fontSize: 9.5, fontWeight: 700, stroke: clr, strokeWidth: 3, paintOrder: 'stroke', opacity: 0.2 }, txt));
                elements.push(React.createElement('text', { key: 'lbl-fg-' + li, x: px + 4, y: py + offsetY,
                    fill: clr, fontSize: 9.5, fontWeight: 700 }, txt));
            });
        }

        return React.createElement('svg', {
            className: 'chan-overlay-svg',
            style: { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 10, overflow: 'visible' }
        }, elements);
    }

    function KlineChartComponent(props) {
        var stockInfo = props.stockInfo || {}, dailyData = props.dailyData || [];
        var showChan = props.showChan !== false;
        var showBi = props.showBi !== false, showZhongshu = props.showZhongshu !== false;
        var showXianduan = props.showXianduan !== false, showLabel = props.showLabel !== false;
        var showMA5 = props.showMA5 !== false, showMA10 = props.showMA10 !== false;
        var showMA20 = props.showMA20 !== false, showMA60 = props.showMA60 !== false;
        var showEXPMA13 = props.showEXPMA13 !== false, showVolume = props.showVolume === true;
        var chartHeight = props.height || 550;

        var chartData = prepareChartData(dailyData);
        var dates = chartData.map(function(d) { return d.trade_date; });

        var chanResult = null;
        if (showChan && chartData.length >= 5) {
            try { chanResult = ChanLunCore.analyze(chartData); } catch(e) { console.warn('[ChanLun] 分析出错:', e); }
        }

        if (chanResult) {
            console.log('[ChanLun] 分析结果: 分型=' + chanResult.stats.fractalCount + ' 笔=' + chanResult.stats.biCount + ' 线段=' + chanResult.stats.xianduanCount + ' 中枢=' + chanResult.stats.zhongshuCount);
            if (chanResult.xianduans && chanResult.xianduans.length > 0) {
                console.log('[ChanLun] 线段详情:', chanResult.xianduans.map(function(x) { return x.direction + ' ' + x.start.date + '→' + x.end.date + '(' + x.biCount + '笔)'; }));
            }
        }

        var allClose = chartData.map(function(d) { return parseFloat(d.close); });
        var allHigh = chartData.map(function(d) { return parseFloat(d.high); });
        var allLow = chartData.map(function(d) { return parseFloat(d.low); });
        var dataMin = Math.min.apply(null, allLow);  // 应该用最低价，不是收盘价
        var dataMax = Math.max.apply(null, allHigh);
        var padding = (dataMax - dataMin) * 0.06;
        var yDomain = [dataMin - padding, dataMax + padding];
        console.log('[KlineChart] yDomain计算: dataMin=' + dataMin + ' dataMax=' + dataMax + ' padding=' + padding + ' yDomain=[' + yDomain[0] + ',' + yDomain[1] + ']');

        var allVol = chartData.map(function(d) { return parseFloat(d.volume || 0); });
        var maxVol = Math.max.apply(null, allVol) || 1;

        var MARGIN = { top: 10, right: 80, left: 5, bottom: 20 };
        var BRUSH_H = 30;  // Brush 高度，用于缩放控制
        var LEGEND_H = 28;
        var VOL_H = showVolume ? 100 : 0;
        var YAXIS_W = 60;

        var containerRef = React.useRef(null);
        var [dimensions, setDimensions] = React.useState({ w: 1200, h: chartHeight });
        var [brushState, setBrushState] = React.useState(function() {
            var defEnd = Math.max(0, dates.length - 1);
            return { start: 0, end: defEnd };
        });

        React.useEffect(function() {
            function measure() {
                if (containerRef.current) {
                    var r = containerRef.current.getBoundingClientRect();
                    setDimensions({ w: r.width, h: r.height });
                }
            }
            measure();
            var ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(measure) : null;
            if (ro && containerRef.current) ro.observe(containerRef.current);
            window.addEventListener('resize', measure);
            return function() {
                window.removeEventListener('resize', measure);
                if (ro) ro.disconnect();
            };
        }, []);

        var plotW = dimensions.w - MARGIN.left - MARGIN.right - YAXIS_W;
        var mainH = Math.max(dimensions.h - (showVolume ? 110 : 10), 250);
        var plotArea = { width: Math.max(plotW, 100), height: Math.max(mainH - MARGIN.top - MARGIN.bottom, 200), left: MARGIN.left + YAXIS_W, top: MARGIN.top };
        var visibleCount = brushState.end - brushState.start + 1;
        var candleBarSize = Math.max(3, Math.min(8, Math.floor(plotW / visibleCount * 0.65)));

        function handleBrushChange(range) {
            console.log('[Brush] onChange 触发:', JSON.stringify(range));
            if (range) {
                var si = range.startIndex !== undefined ? range.startIndex : range.start;
                var ei = range.endIndex !== undefined ? range.endIndex : range.end;
                if (typeof si === 'number' && typeof ei === 'number') {
                    console.log('[Brush] 更新范围:', si, '-', ei);
                    setBrushState({ start: si, end: ei });
                }
            }
        }

        function handleZoomIn() {
            var mid = Math.floor((brushState.start + brushState.end) / 2);
            var rangeLen = brushState.end - brushState.start;
            var newLen = Math.max(10, Math.ceil(rangeLen * 0.6));
            var newStart = Math.max(0, mid - Math.floor(newLen / 2));
            var newEnd = Math.min(dates.length - 1, newStart + newLen);
            if (newEnd - newStart < 10) { newEnd = Math.min(dates.length - 1, newStart + 10); }
            console.log('[Zoom] 放大:', newStart, '-', newEnd);
            setBrushState({ start: newStart, end: newEnd });
        }

        function handleZoomOut() {
            var padding = Math.floor(dates.length * 0.05);
            setBrushState({ start: 0, end: dates.length - 1 });
            console.log('[Zoom] 重置: 全部数据');
        }

        function handlePanLeft() {
            var shift = Math.ceil((brushState.end - brushState.start) * 0.3);
            var newStart = Math.max(0, brushState.start - shift);
            var newEnd = Math.min(dates.length - 1, newStart + (brushState.end - brushState.start));
            if (newEnd === dates.length - 1) { newStart = Math.max(0, newEnd - (brushState.end - brushState.start)); }
            setBrushState({ start: newStart, end: newEnd });
        }

        function handlePanRight() {
            var shift = Math.ceil((brushState.end - brushState.start) * 0.3);
            var newEnd = Math.min(dates.length - 1, brushState.end + shift);
            var newStart = Math.max(0, newEnd - (brushState.end - brushState.start));
            setBrushState({ start: newStart, end: newEnd });
        }

        var chartChildren = [];

        chartChildren.push(React.createElement(CartesianGrid, { key: 'grid',
            stroke: '#f1f5f9', strokeWidth: 0.5,
            strokeDasharray: '3 3',
            vertical: false
        }));

        chartChildren.push(React.createElement(XAxis, { key: 'xaxis',
            dataKey: 'trade_date',
            tick: { fontSize: 11, fill: '#64748b' },
            interval: 'preserveStartEnd',
            minTickGap: 50,
            axisLine: { stroke: '#cbd5e1', strokeWidth: 1 },
            tickLine: { stroke: '#f1f5f9', strokeWidth: 0.5, strokeDasharray: '3 3' },
            tickFormatter: function(v) { return String(v).replace(/(\d{4})(\d{2})(\d{2})/, '$1/$2/$3'); }
        }));

        chartChildren.push(React.createElement(YAxis, { key: 'yaxis',
            domain: [yDomain[0], yDomain[1]],
            tick: { fontSize: 11, fill: '#64748b', fontVariantNumeric: 'tabular-nums' },
            tickFormatter: function(v) { var n = Number(v); return (n % 1 === 0) ? n.toFixed(0) : n.toFixed(2); },
            width: YAXIS_W,
            axisLine: { stroke: '#cbd5e1', strokeWidth: 1 },
            tickLine: { stroke: '#f1f5f9', strokeWidth: 0.5, strokeDasharray: '3 3' }
        }));

        if (showVolume) {
            var volDomain = [0, Math.max.apply(null, allVol) * 1.05];
        }

        chartChildren.push(React.createElement(Brush, { key: 'brush',
            dataKey: 'trade_date',
            startIndex: brushState.start,
            endIndex: brushState.end,
            height: BRUSH_H,
            fill: 'rgba(99,102,241,0.08)',
            stroke: '#6366f1',
            strokeWidth: 1.5,
            onChange: handleBrushChange
        }));

        // 使用 Bar 组件绘制蜡烛图 - dataKey用close但shape中忽略，基于yDomain重新计算
        chartChildren.push(React.createElement(Bar, { key: 'candle',
            dataKey: 'close',
            shape: function(p) { return CandlestickShape(Object.assign({}, p, { yDomain: yDomain, plotH: mainH_px - MARGIN.top - MARGIN.bottom })); },
            isAnimationActive: false,
            barSize: candleBarSize,
            name: 'K线',
            fill: '#8884d8'
        }));

        if (showMA5) chartChildren.push(React.createElement(Line, { key: 'ma5', type: 'monotone', dataKey: '_ma5', stroke: '#f97316', dot: false, strokeWidth: 1.0, connectNulls: false, name: 'MA5', hide: false }));
        if (showMA10) chartChildren.push(React.createElement(Line, { key: 'ma10', type: 'monotone', dataKey: '_ma10', stroke: '#06b6d4', dot: false, strokeWidth: 1.0, connectNulls: false, name: 'MA10', hide: false }));
        if (showMA20) chartChildren.push(React.createElement(Line, { key: 'ma20', type: 'monotone', dataKey: '_ma20', stroke: '#8b5cf6', dot: false, strokeWidth: 1.0, connectNulls: false, name: 'MA20', hide: false }));
        if (showMA60) chartChildren.push(React.createElement(Line, { key: 'ma60', type: 'monotone', dataKey: '_ma60', stroke: '#eab308', dot: false, strokeWidth: 1.0, connectNulls: false, name: 'MA60', hide: false }));
        if (showEXPMA13) chartChildren.push(React.createElement(Line, { key: 'expma13', type: 'monotone', dataKey: '_expma13', stroke: '#ffaa00', dot: false, strokeWidth: 1.2, connectNulls: false, name: 'EXPMA13', hide: false }));



        chartChildren.push(React.createElement(Tooltip, { key: 'tooltip',
            content: CustomTooltip,
            cursor: { stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4' }
        }));

        chartChildren.push(React.createElement(Legend, { key: 'legend',
            iconType: 'plainbar', iconSize: 10,
            wrapperStyle: { fontSize: 10, paddingTop: 6 }
        }));

        var zoomBtnStyle = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 24, borderRadius: 4, border: '1px solid #e2e8f0', background: '#fff', color: '#475569', fontSize: 13, cursor: 'pointer', margin: '0 2px' };
        var rangeInfo = (brushState.end - brushState.start + 1) + '/' + dates.length;
        var mainH_px = showVolume ? chartHeight - 110 : chartHeight - 10;
        var volH_px = showVolume ? 95 : 0;

        var mainChart = React.createElement('div', { key: 'main-wrap', style: { position: 'relative', width: '100%', height: mainH_px } },
            React.createElement(ResponsiveContainer, { width: '100%', height: '100%' },
                React.createElement(ComposedChart, {
                    data: chartData, margin: MARGIN, syncId: 'chanlunKline'
                }, chartChildren)
            ),
            chanResult ? React.createElement(ChanOverlay, {
                biData: chanResult.bis,
                zhongshuData: chanResult.zhongshus,
                xianduanData: chanResult.xianduans,
                showBi: showBi,
                showZhongshu: showZhongshu,
                showXianduan: showXianduan,
                showLabel: showLabel,
                dates: dates,
                plotArea: { width: plotW, height: mainH_px - MARGIN.top - MARGIN.bottom, left: MARGIN.left + YAXIS_W, top: MARGIN.top },
                yMin: yDomain[0],
                yMax: yDomain[1],
                brushRange: brushState
            }) : null
        );

        var volChart = null;
        if (showVolume && volDomain) {
            volChart = React.createElement('div', { key: 'vol-wrap', style: { width: '100%', height: volH_px, marginTop: 5 } },
                React.createElement(ResponsiveContainer, { width: '100%', height: '100%' },
                    React.createElement(ComposedChart, {
                        data: chartData, margin: { top: 2, right: 80, left: 5, bottom: 5 }, syncId: 'chanlunKline'
                    },
                        React.createElement(XAxis, { dataKey: 'trade_date',
                            tick: { fill: '#64748b', fontSize: 9 }, interval: 'preserveStartEnd',
                            axisLine: { stroke: '#cbd5e1', strokeWidth: 1 },
                            tickLine: { stroke: '#f1f5f9', strokeWidth: 0.5, strokeDasharray: '3 3' },
                            tickFormatter: function(v) { return String(v).replace(/(\d{4})(\d{2})(\d{2})/, '$1/$2/$3'); }
                        }),
                        React.createElement(YAxis, { yAxisId: 'vol', orientation: 'right',
                            domain: volDomain,
                            tick: { fill: '#64748b', fontSize: 9 }, width: YAXIS_W,
                            tickFormatter: function(v) { var n = Number(v); return n >= 10000 ? (n/10000).toFixed(0)+'万' : n.toFixed(0); }
                        }),
                        React.createElement(CartesianGrid, { strokeDasharray: '3 3', stroke: '#f1f5f9' }),
                        React.createElement(Bar, { yAxisId: 'vol', dataKey: 'volume',
                            shape: function(p) { return VolumeBarShape(Object.assign({}, p, { maxVol: volDomain[1] / 1.05 })); },
                            barSize: Math.max(2, candleBarSize * 0.5), isAnimationActive: false, opacity: 0.55
                        })
                    )
                )
            );
        }

        return React.createElement('div', {
            ref: containerRef,
            className: 'chanlun-chart-wrapper',
            style: { position: 'relative', width: '100%', height: chartHeight, overflow: 'visible' }
        },
            React.createElement('div', { style: { position: 'absolute', top: 2, right: 6, zIndex: 20, display: 'flex', alignItems: 'center', gap: 2, background: 'rgba(255,255,255,0.92)', padding: '2px 6px', borderRadius: 6, border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' } },
                React.createElement('span', { style: { fontSize: 10, color: '#64748b', marginRight: 4, fontVariantNumeric: 'tabular-nums', fontFamily: 'monospace' } }, rangeInfo),
                React.createElement('button', { style: zoomBtnStyle, title: '缩小(复位)', onClick: handleZoomOut }, '⊞'),
                React.createElement('button', { style: zoomBtnStyle, title: '放大', onClick: handleZoomIn }, '🔍+'),
                React.createElement('button', { style: zoomBtnStyle, title: '左移', onClick: handlePanLeft }, '◀'),
                React.createElement('button', { style: zoomBtnStyle, title: '右移', onClick: handlePanRight }, '▶')
            ),
            mainChart,
            volChart
        );
    }

    function renderToContainer(containerId, stockInfo, dailyData, options) {
        var opts = options || {};
        var container = document.getElementById(containerId);
        if (!container) { console.error('[ChanLunKline] 容器未找到:', containerId); return null; }
        if (container._reactRoot) { try { container._reactRoot.unmount(); } catch(e) {} }

        var root = ReactDOM.createRoot(container);
        container._reactRoot = root;
        root.render(React.createElement(KlineChartComponent, {
            stockInfo: stockInfo, dailyData: dailyData,
            height: opts.height || 560,
            showChan: opts.showChan !== undefined ? opts.showChan : true,
            showBi: opts.showBi, showZhongshu: opts.showZhongshu,
            showXianduan: opts.showXianduan, showLabel: opts.showLabel,
            showMA5: opts.showMA5, showMA10: opts.showMA10,
            showMA20: opts.showMA20, showMA60: opts.showMA60,
            showEXPMA13: opts.showEXPMA13, showVolume: opts.showVolume
        }));

        window._chanLunLastResult = null;
        if (opts.showChan !== false && dailyData && dailyData.length >= 5) {
            try {
                var cd = prepareChartData(dailyData);
                window._chanLunLastResult = ChanLunCore.analyze(cd);
                console.log('[ChanLun] 分析完成:', window._chanLunLastResult.stats);
            } catch(e) {}
        }
        return root;
    }

    return {
        KlineChartComponent: KlineChartComponent,
        renderToContainer: renderToContainer,
        CandlestickShape: CandlestickShape,
        VolumeBarShape: VolumeBarShape,
        CustomTooltip: CustomTooltip,
        ChanOverlay: ChanOverlay,
        prepareChartData: prepareChartData,
        calcMA: calcMA,
        calcEXPMA: calcEXPMA
    };
})();
