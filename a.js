// 全局变量存储捕获的文本
window.capturedText = null;

// 保存原始方法
const originalExecCommand = document.execCommand;

// 覆盖 execCommand
document.execCommand = function(command, ...args) {
    if (command.toLowerCase() === 'copy') {
        // 获取当前选中的文本
        const selection = window.getSelection();
        const selectedText = selection.toString();

        if (selectedText) {
            // 存储到全局变量
            window.capturedText = selectedText;
            console.log('捕获的文本:', selectedText);
        }

        // 阻止实际复制到剪贴板
        return true; // 返回 true 模拟成功
    }
    // 其他命令正常执行
    return originalExecCommand.apply(this, [command, ...args]);
};