
class TabManager {
    constructor() {
        this.tabs = document.querySelectorAll('#profile-tabs .tab');
        this.contents = document.querySelectorAll('.tab-content');
        this.init();
    }

    init() {
        this.activateTab(this.tabs[0]);
        this.tabs.forEach(tab => {
            tab.addEventListener('click', () => this.activateTab(tab));
        });
    }

    activateTab(selectedTab) {
        this.tabs.forEach(tab => tab.classList.remove('tab-active'));
        selectedTab.classList.add('tab-active');

        this.contents.forEach(content => content.classList.add('hidden'));
        const contentId = selectedTab.getAttribute('data-content');
        document.getElementById(contentId)?.classList.remove('hidden');
    }
}