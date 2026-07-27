/** @odoo-module **/

import { Component, useRef, onMounted, onPatched, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CommissionGraph extends Component {

    static template = "sales_commission.CommissionGraph";

    static props = { ...standardFieldProps };

    setup() {

        this.canvasRef = useRef("canvas");

        onMounted(() => this.deferredDraw());

        onPatched(() => this.deferredDraw());

        this.onResize = () => this.drawGraph();

        window.addEventListener("resize", this.onResize);

        onWillUnmount(() => {
            window.removeEventListener("resize", this.onResize);
        });

    }

    /**
     * onMounted/onPatched can fire before the browser has finished
     * laying out the page, so canvas.parentElement.clientWidth may
     * still read as 0 at that exact instant (this is why the graph
     * only ever appeared once something else, like opening DevTools
     * or resizing the window, forced a layout recalculation).
     * Waiting two animation frames reliably lands after layout has
     * settled.
     */
    deferredDraw() {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.drawGraph();
            });
        });
    }

    /**
     * Pull the commission levels straight from the record's own
     * reactive data instead of scraping rendered table text. This
     * is always in sync with what Odoo actually holds for this
     * record, with no timing race against the list widget's render.
     */
    getCommissionData() {

        const field = this.props.record.data[this.props.name];

        const records = (field && field.records) || [];

        const data = records
            .map((r) => ({
                target: r.data.target_completion,
                commission: r.data.commission,
            }))
            .filter(
                (d) =>
                    typeof d.target === "number" &&
                    typeof d.commission === "number"
            );

        data.sort((a, b) => a.target - b.target);

        return data;

    }

    drawGraph() {

        const canvas = this.canvasRef.el;

        if (!canvas) {
            return;
        }

        const parent = canvas.parentElement;

        canvas.width = parent.clientWidth;
        canvas.height = 340;

        const ctx = canvas.getContext("2d");

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const data = this.getCommissionData();

        if (!data.length) {
            this.drawEmptyMessage(ctx, canvas);
            return;
        }

        this.drawFullGraph(ctx, canvas, data);

    }

    drawEmptyMessage(ctx, canvas) {

        ctx.font = "15px Arial";
        ctx.fillStyle = "#777";
        ctx.textAlign = "center";

        ctx.fillText(
            "No commission levels",
            canvas.width / 2,
            canvas.height / 2
        );

    }

    drawFullGraph(ctx, canvas, data) {

        const padding = { left: 60, right: 30, top: 25, bottom: 45 };

        const left = padding.left;
        const right = canvas.width - padding.right;
        const top = padding.top;
        const bottom = canvas.height - padding.bottom;

        const graphWidth = right - left;
        const graphHeight = bottom - top;

        const maxTarget = 150;

        const maxCommission = Math.max(
            ...data.map((d) => d.commission),
            1000
        );

        ctx.strokeStyle = "#ECECEC";
        ctx.lineWidth = 1;

        for (let i = 0; i <= 4; i++) {
            const y = bottom - (graphHeight * i) / 4;
            ctx.beginPath();
            ctx.moveTo(left, y);
            ctx.lineTo(right, y);
            ctx.stroke();
        }

        for (let i = 0; i <= 3; i++) {
            const x = left + (graphWidth * i) / 3;
            ctx.beginPath();
            ctx.moveTo(x, top);
            ctx.lineTo(x, bottom);
            ctx.stroke();
        }

        ctx.strokeStyle = "#BBBBBB";
        ctx.lineWidth = 2;

        ctx.beginPath();
        ctx.moveTo(left, top);
        ctx.lineTo(left, bottom);
        ctx.lineTo(right, bottom);
        ctx.stroke();

        const points = data.map((row) => ({
            x: left + (row.target / maxTarget) * graphWidth,
            y: bottom - (row.commission / maxCommission) * graphHeight,
        }));

        if (points.length) {
            const last = data[data.length - 1];
            if (last.target < 150) {
                points.push({
                    x: left + graphWidth,
                    y: points[points.length - 1].y,
                });
            }
        }

        ctx.beginPath();
        ctx.moveTo(points[0].x, bottom);

        points.forEach((p) => ctx.lineTo(p.x, p.y));

        ctx.lineTo(points[points.length - 1].x, bottom);
        ctx.closePath();

        const gradient = ctx.createLinearGradient(0, top, 0, bottom);
        gradient.addColorStop(0, "rgba(46,134,222,.35)");
        gradient.addColorStop(1, "rgba(46,134,222,0)");

        ctx.fillStyle = gradient;
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);

        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }

        ctx.strokeStyle = "#2E86DE";
        ctx.lineWidth = 3;
        ctx.stroke();

        ctx.fillStyle = "#2E86DE";

        points.forEach((p) => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
            ctx.fill();
        });

        ctx.fillStyle = "#666";
        ctx.font = "13px Arial";
        ctx.textAlign = "center";

        [0, 50, 100, 150].forEach((value) => {
            const x = left + (value / maxTarget) * graphWidth;
            ctx.fillText(value + "%", x, bottom + 22);
        });

        ctx.textAlign = "right";

        for (let i = 0; i <= 4; i++) {
            const value = Math.round((maxCommission * i) / 4);
            const y = bottom - (graphHeight * i) / 4;
            ctx.fillText(value.toLocaleString(), left - 8, y + 5);
        }

    }

}

registry.category("fields").add("commission_graph", {
    component: CommissionGraph,
    supportedTypes: ["one2many"],
});