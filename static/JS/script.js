const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

const socket = io();

let isDrawing = false;
let lastX, lastY;

canvas.onmousedown = (e) => {
    isDrawing = true;
    lastX = e.offsetX;
    lastY = e.offsetY;
};

canvas.onmousemove = (e) => {
    if (isDrawing) {
        drawLine(lastX, lastY, e.offsetX, e.offsetY);
        sendDrawingData(lastX, lastY, e.offsetX, e.offsetY);
        lastX = e.offsetX;
        lastY = e.offsetY;
    }
};

canvas.onmouseup = () => {
    isDrawing = false;
};

function drawLine(x1, y1, x2, y2) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
}

function sendDrawingData(x1, y1, x2, y2) {
    socket.emit('drawing', { x1, y1, x2, y2 });
}

socket.on('drawing', (data) => {
    drawLine(data.x1, data.y1, data.x2, data.y2);
});

