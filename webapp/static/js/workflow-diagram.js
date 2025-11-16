// ===== Workflow Diagram with Interactive Nodes =====

class WorkflowDiagram {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.uploadValidated = sessionStorage.getItem('uploadValidated') === 'true';
        
        // Node definitions
        this.nodes = [
            // Input Data Nodes
            { id: 'sales', label: 'Sales Data', type: 'input', x: 100, y: 100, file: 'get_sales.csv' },
            { id: 'inventory', label: 'Inventory Data', type: 'input', x: 100, y: 200, file: 'get_inventory.csv' },
            { id: 'price_opt', label: 'Price Optimizer', type: 'input', x: 100, y: 300, file: 'price_optimizer.csv' },
            { id: 'marketing', label: 'Marketing Planner', type: 'input', x: 100, y: 400, file: 'marketing_planner.csv' },
            { id: 'labor', label: 'Labor Simulator', type: 'input', x: 100, y: 500, file: 'labor_simulator.csv' },
            
            // Agent Nodes
            { id: 'trigger', label: 'Trigger Agent', type: 'agent', x: 400, y: 150, description: 'Detects underperforming SKUs' },
            { id: 'pricing', label: 'Pricing Agent', type: 'agent', x: 700, y: 150, description: 'Proposes optimal prices' },
            { id: 'marketing_agent', label: 'Marketing Agent', type: 'agent', x: 700, y: 300, description: 'Recommends campaigns' },
            { id: 'labor_agent', label: 'Labor Agent', type: 'agent', x: 1000, y: 225, description: 'Estimates labor costs' },
            { id: 'finance', label: 'Finance Agent', type: 'agent', x: 1300, y: 225, description: 'Ranks action plans' },
            { id: 'product', label: 'Product Agent', type: 'agent', x: 1300, y: 375, description: 'Validates SKU feedback' },
            { id: 'governance', label: 'Governance Agent', type: 'agent', x: 1600, y: 300, description: 'Finalizes actions' },
            
            // Output Data Nodes
            { id: 'flagged', label: 'Flagged SKUs', type: 'output', x: 400, y: 350, file: 'flagged_skus.csv' },
            { id: 'choice_sets', label: 'Choice Sets', type: 'output', x: 400, y: 450, file: 'choice_sets.json' },
            { id: 'price_scenarios', label: 'Price Scenarios', type: 'output', x: 1000, y: 50, file: 'price_scenarios.csv' },
            { id: 'campaigns', label: 'Campaign Scenarios', type: 'output', x: 1000, y: 400, file: 'campaign_scenarios.csv' },
            { id: 'labor_costs', label: 'Labor Costs', type: 'output', x: 1300, y: 100, file: 'labor_cost_estimates.csv' },
            { id: 'ranked_plan', label: 'Ranked Action Plan', type: 'output', x: 1600, y: 150, file: 'ranked_action_plan.csv' },
            { id: 'product_feedback', label: 'Product Feedback', type: 'output', x: 1600, y: 450, file: 'product_feedback.csv' },
            { id: 'final_actions', label: 'Final Actions', type: 'output', x: 1900, y: 300, file: 'finalized_actions.csv' }
        ];
        
        // Edge definitions (connections between nodes)
        this.edges = [
            // Input to Trigger Agent
            { from: 'sales', to: 'trigger' },
            { from: 'inventory', to: 'trigger' },
            
            // Trigger outputs
            { from: 'trigger', to: 'flagged' },
            { from: 'trigger', to: 'choice_sets' },
            
            // Flagged SKUs to Pricing and Marketing
            { from: 'flagged', to: 'pricing' },
            { from: 'flagged', to: 'marketing_agent' },
            
            // Price optimizer to Pricing
            { from: 'price_opt', to: 'pricing' },
            
            // Marketing planner to Marketing Agent
            { from: 'marketing', to: 'marketing_agent' },
            
            // Pricing outputs
            { from: 'pricing', to: 'price_scenarios' },
            
            // Marketing outputs
            { from: 'marketing_agent', to: 'campaigns' },
            
            // Price and Campaign scenarios to Labor
            { from: 'price_scenarios', to: 'labor_agent' },
            { from: 'campaigns', to: 'labor_agent' },
            { from: 'labor', to: 'labor_agent' },
            
            // Labor outputs
            { from: 'labor_agent', to: 'labor_costs' },
            
            // Labor costs to Finance
            { from: 'labor_costs', to: 'finance' },
            { from: 'price_scenarios', to: 'finance' },
            { from: 'campaigns', to: 'finance' },
            
            // Finance outputs
            { from: 'finance', to: 'ranked_plan' },
            
            // Ranked plan to Product
            { from: 'ranked_plan', to: 'product' },
            
            // Product outputs
            { from: 'product', to: 'product_feedback' },
            
            // Final to Governance
            { from: 'ranked_plan', to: 'governance' },
            { from: 'product_feedback', to: 'governance' },
            
            // Governance outputs
            { from: 'governance', to: 'final_actions' }
        ];
        
        this.initCanvas();
        this.setupEventListeners();
        this.draw();
    }
    
    initCanvas() {
        // Set canvas size
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
    }
    
    setupEventListeners() {
        // Mouse events for panning
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', () => this.handleMouseUp());
        this.canvas.addEventListener('mouseleave', () => this.handleMouseUp());
        
        // Double click to view node data (only if validated)
        this.canvas.addEventListener('dblclick', (e) => this.handleDoubleClick(e));
        
        // Zoom buttons
        document.getElementById('zoomInBtn').addEventListener('click', () => this.zoom(1.2));
        document.getElementById('zoomOutBtn').addEventListener('click', () => this.zoom(0.8));
        document.getElementById('resetZoomBtn').addEventListener('click', () => this.resetView());
        
        // React to upload validation within this tab session
        window.addEventListener('ims:uploadValidated', () => {
            this.uploadValidated = true;
            this.draw();
        });

        // Resize canvas on window resize
        window.addEventListener('resize', () => {
            this.initCanvas();
            this.draw();
        });
    }
    
    handleMouseDown(e) {
        this.isDragging = true;
        this.dragStartX = e.clientX - this.offsetX;
        this.dragStartY = e.clientY - this.offsetY;
    }
    
    handleMouseMove(e) {
        if (this.isDragging) {
            this.offsetX = e.clientX - this.dragStartX;
            this.offsetY = e.clientY - this.dragStartY;
            this.draw();
        }
    }
    
    handleMouseUp() {
        this.isDragging = false;
    }
    
    handleDoubleClick(e) {
        // Block interactions if not validated this session
        if (!this.uploadValidated) {
            return;
        }
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left - this.offsetX) / this.scale;
        const y = (e.clientY - rect.top - this.offsetY) / this.scale;
        
        // Find clicked node
        const node = this.nodes.find(n => {
            const nodeWidth = 140;
            const nodeHeight = 60;
            return x >= n.x && x <= n.x + nodeWidth && y >= n.y && y <= n.y + nodeHeight;
        });
        
        if (node && node.file) {
            this.viewNodeData(node);
        }
    }
    
    zoom(factor) {
        this.scale *= factor;
        this.scale = Math.max(0.5, Math.min(2, this.scale)); // Limit zoom between 0.5x and 2x
        this.draw();
    }
    
    resetView() {
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.draw();
    }
    
    draw() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Save context
        this.ctx.save();
        
        // Apply transformations
        this.ctx.translate(this.offsetX, this.offsetY);
        this.ctx.scale(this.scale, this.scale);
        
        // Draw edges first (so they appear behind nodes)
        this.drawEdges();
        
        // Draw nodes
        this.drawNodes();

        // If not validated, overlay a subtle lock message
        if (!this.uploadValidated) {
            this.ctx.save();
            this.ctx.fillStyle = 'rgba(0,0,0,0.55)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.fillStyle = '#FFFFFF';
            this.ctx.font = '600 18px Inter, sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('Upload all required CSV files to enable interactive diagram', this.canvas.width/2, this.canvas.height/2);
            this.ctx.restore();
        }
        
        // Restore context
        this.ctx.restore();
    }
    
    drawEdges() {
        this.edges.forEach(edge => {
            const fromNode = this.nodes.find(n => n.id === edge.from);
            const toNode = this.nodes.find(n => n.id === edge.to);
            
            if (fromNode && toNode) {
                this.ctx.beginPath();
                this.ctx.strokeStyle = '#9CA3AF';
                this.ctx.lineWidth = 2;
                
                // Calculate connection points (center right of from node to center left of to node)
                const fromX = fromNode.x + 140;
                const fromY = fromNode.y + 30;
                const toX = toNode.x;
                const toY = toNode.y + 30;
                
                // Draw curved line
                const midX = (fromX + toX) / 2;
                this.ctx.moveTo(fromX, fromY);
                this.ctx.bezierCurveTo(midX, fromY, midX, toY, toX, toY);
                this.ctx.stroke();
                
                // Draw arrow
                this.drawArrow(toX, toY, Math.atan2(toY - fromY, toX - fromX));
            }
        });
    }
    
    drawArrow(x, y, angle) {
        const arrowSize = 10;
        this.ctx.save();
        this.ctx.translate(x, y);
        this.ctx.rotate(angle);
        this.ctx.beginPath();
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(-arrowSize, -arrowSize / 2);
        this.ctx.lineTo(-arrowSize, arrowSize / 2);
        this.ctx.closePath();
        this.ctx.fillStyle = '#9CA3AF';
        this.ctx.fill();
        this.ctx.restore();
    }
    
    drawNodes() {
        this.nodes.forEach(node => {
            const x = node.x;
            const y = node.y;
            const width = 140;
            const height = 60;
            const radius = 8;
            
            // Set colors based on node type
            let bgColor, borderColor, textColor;
            if (node.type === 'input') {
                bgColor = '#EEF2FF';
                borderColor = '#4F46E5';
                textColor = '#4F46E5';
            } else if (node.type === 'agent') {
                bgColor = '#D1FAE5';
                borderColor = '#10B981';
                textColor = '#065F46';
            } else {
                bgColor = '#FEF3C7';
                borderColor = '#F59E0B';
                textColor = '#92400E';
            }
            
            // Draw rounded rectangle
            this.ctx.beginPath();
            this.ctx.moveTo(x + radius, y);
            this.ctx.lineTo(x + width - radius, y);
            this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
            this.ctx.lineTo(x + width, y + height - radius);
            this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
            this.ctx.lineTo(x + radius, y + height);
            this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
            this.ctx.lineTo(x, y + radius);
            this.ctx.quadraticCurveTo(x, y, x + radius, y);
            this.ctx.closePath();
            
            // Fill and stroke
            this.ctx.fillStyle = bgColor;
            this.ctx.fill();
            this.ctx.strokeStyle = borderColor;
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
            
            // Draw text
            this.ctx.fillStyle = textColor;
            this.ctx.font = 'bold 12px Inter, sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(node.label, x + width / 2, y + height / 2);
            
            // Draw icon indicator if it has a file
            if (node.file) {
                this.ctx.font = '10px FontAwesome';
                this.ctx.fillText('📄', x + width - 15, y + 15);
            }
        });
    }
    
    async viewNodeData(node) {
        if (!node.file) return;
        
        showLoading();
        
        try {
            // Check if it's an input or output file
            const isInput = node.type === 'input';
            const filePath = isInput ? `/preview-input/${node.file}` : `/preview/${node.file}`;
            
            const response = await fetch(filePath);
            const data = await response.json();
            
            hideLoading();
            
            if (data.success) {
                previewTitle.textContent = node.label + ' - ' + node.file;
                
                if (node.file.endsWith('.csv')) {
                    const table = createPreviewTable(data.data);
                    previewContent.innerHTML = table;
                } else if (node.file.endsWith('.json')) {
                    previewContent.innerHTML = `<pre>${JSON.stringify(data.data, null, 2)}</pre>`;
                }
                
                previewModal.style.display = 'flex';
            } else {
                alert('Data not available yet. Please run the workflow first.');
            }
        } catch (error) {
            hideLoading();
            alert('Failed to load data: ' + error.message);
        }
    }
}

// Initialize diagram when page loads
let workflowDiagram;
document.addEventListener('DOMContentLoaded', function() {
    workflowDiagram = new WorkflowDiagram('workflowCanvas');
});
