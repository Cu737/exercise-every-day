const body = document.querySelector('body')
const sidebar = body.querySelector('nav')
const toggle = body.querySelector('.toggle')
const searchBtn = body.querySelector('.search-box')
const modeSwitch = body.querySelector('.toggle-switch')
const modeText = body.querySelector('.mode-text')
const gameLink = document.querySelector('#game');
const homecss = document.querySelector('link.homecss');
toggle.addEventListener('click', () => {
    sidebar.classList.toggle('close')
})
searchBtn.addEventListener('click', () => {
    sidebar.classList.remove('close')
})
modeSwitch.addEventListener('click', () => {
    body.classList.toggle('dark');
    if (body.classList.contains('dark')) {
        modeText.innerText = "Light mode"
        // 更改子网页的css
        homecss.setAttribute('href', homedarkcssPath);

    } else {
        modeText.innerText = "Dark mode"
        setTimeout(() => {
            homecss.setAttribute('href', homecssPath);
        }, 0); // 延时500毫秒执行

    }


})