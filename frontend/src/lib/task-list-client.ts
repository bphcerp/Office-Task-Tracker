export type StatusFilter = 'all' | 'todo' | 'progress' | 'done';

export type SortKey =
  | 'received-desc'
  | 'received-asc'
  | 'created-desc'
  | 'title-asc'
  | 'title-desc';

export function compareItems(a: HTMLElement, b: HTMLElement, sort: SortKey): number {
  switch (sort) {
    case 'received-desc':
      return dateValue(b.dataset.received) - dateValue(a.dataset.received);
    case 'received-asc':
      return dateValue(a.dataset.received) - dateValue(b.dataset.received);
    case 'created-desc':
      return dateValue(b.dataset.created) - dateValue(a.dataset.created);
    case 'title-asc':
      return (a.dataset.title ?? '').localeCompare(b.dataset.title ?? '');
    case 'title-desc':
      return (b.dataset.title ?? '').localeCompare(a.dataset.title ?? '');
    default:
      return 0;
  }
}

function dateValue(value: string | undefined): number {
  if (!value) return 0;
  const ms = Date.parse(value);
  return Number.isNaN(ms) ? 0 : ms;
}

export function matchesSearch(item: HTMLElement, query: string): boolean {
  if (!query) return true;
  return (item.dataset.search ?? '').includes(query);
}

export function matchesStatus(item: HTMLElement, status: StatusFilter): boolean {
  if (status === 'all') return true;
  return item.dataset.tone === status;
}

export function initTaskBrowser(root: HTMLElement): void {
  const list = root.querySelector<HTMLUListElement>('.task-list');
  const countEl = root.querySelector<HTMLElement>('.task-count');
  const noResultsEl = root.querySelector<HTMLElement>('.task-no-results');
  const searchInput = root.querySelector<HTMLInputElement>('[data-task-search]');
  const sortSelect = root.querySelector<HTMLSelectElement>('[data-task-sort]');
  const filterGroup = root.querySelector<HTMLElement>('[data-task-filters]');

  if (!list || !countEl || !noResultsEl || !searchInput || !sortSelect || !filterGroup) {
    return;
  }

  const items = () => [...list.querySelectorAll<HTMLLIElement>('.task-list__item')];
  const total = items().length;
  let statusFilter: StatusFilter = 'all';

  function apply(): void {
    const query = searchInput.value.trim().toLowerCase();
    const sort = sortSelect.value as SortKey;

    const visible = items()
      .filter((item) => matchesStatus(item, statusFilter) && matchesSearch(item, query))
      .sort((a, b) => compareItems(a, b, sort));

    for (const item of items()) {
      item.hidden = true;
    }
    for (const item of visible) {
      item.hidden = false;
      list.appendChild(item);
    }

    const filtered = query !== '' || statusFilter !== 'all';
    if (filtered) {
      countEl.textContent = `${visible.length} of ${total} task${total === 1 ? '' : 's'}`;
    } else {
      countEl.textContent = `${total} task${total === 1 ? '' : 's'}`;
    }

    noResultsEl.hidden = visible.length > 0;
  }

  searchInput.addEventListener('input', apply);
  sortSelect.addEventListener('change', apply);

  filterGroup.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    if (!target.matches('[data-status-filter]')) return;

    statusFilter = target.dataset.statusFilter as StatusFilter;

    for (const button of filterGroup.querySelectorAll<HTMLButtonElement>('[data-status-filter]')) {
      const active = button === target;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', String(active));
    }

    apply();
  });

  apply();
}
