export function createSidebarController(workspace: HTMLElement, toggle: HTMLButtonElement) {
  const setCollapsed = (collapsed: boolean) => { workspace.classList.toggle('sidebar-collapsed', collapsed); toggle.setAttribute('aria-expanded', String(!collapsed)); };
  toggle.addEventListener('click', () => setCollapsed(!workspace.classList.contains('sidebar-collapsed')));
  return { collapse: () => setCollapsed(true), toggle: () => setCollapsed(!workspace.classList.contains('sidebar-collapsed')) };
}
