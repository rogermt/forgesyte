---
name: react-compositional
description: "Create functional, compositional React components using headless UI patterns with decoupled state management. Use when building React components that need: (1) Composition over complex prop APIs, (2) Separation of logic from presentation (headless patterns), (3) Pure, idempotent rendering, (4) Compound component APIs, (5) Integration with react-query for server state, or (6) Support for both controlled and uncontrolled patterns. Ideal for building flexible, reusable component libraries and data-driven UIs."
---

# React Compositional Components

Build functional, compositional React components following headless UI patterns with proper state separation and react-query integration.

## Core Workflow

When creating compositional components:

1. **Identify state types** - Separate UI state from server state
2. **Extract logic to hooks** - Create headless hooks for reusable logic  
3. **Design composition API** - Plan how components combine (compound, slots, render props)
4. **Implement pure components** - Ensure idempotency and no side effects in render
5. **Integrate react-query** - Add server state management where needed
6. **Support both patterns** - Allow controlled and uncontrolled usage

## State Management Strategy

### UI State vs Server State

**UI State** (component-local):
- Modal open/closed
- Selected tab
- Highlighted index
- Form draft values
- Use: `useState`, `useReducer`, context

**Server State** (react-query):
- User data from API
- Product listings
- Search results
- Posted form submissions
- Use: `useQuery`, `useMutation`, `useInfiniteQuery`

Keep these concerns strictly separated.

## Design Patterns

### Choose the Right Pattern

**Compound Components** - When sub-components work together:
```typescript
<Tabs>
  <Tabs.List>
    <Tabs.Tab value="a">Tab A</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel value="a">Content A</Tabs.Panel>
</Tabs>
```

**Render Props** - When consumers need full control:
```typescript
<DataList data={users}>
  {(user) => <UserCard user={user} />}
</DataList>
```

**Headless Hook** - When logic is reusable without UI:
```typescript
const { isOpen, toggle } = useDisclosure();
```

### Implementation Guidelines

**Create Context for Compound Components:**
```typescript
const Context = createContext<ContextValue | null>(null);

function useComponentContext() {
  const ctx = useContext(Context);
  if (!ctx) throw new Error('Must use within Parent');
  return ctx;
}
```

**Extract Headless Logic:**
```typescript
function useComponentLogic(props) {
  // All stateful logic here
  return { state, actions };
}

function Component(props) {
  const logic = useComponentLogic(props);
  return <UI {...logic} />;
}
```

**Support Controlled/Uncontrolled:**
```typescript
function Component({ value, defaultValue, onChange }) {
  const [internal, setInternal] = useState(defaultValue);
  const isControlled = value !== undefined;
  const current = isControlled ? value : internal;
  
  const handleChange = (newValue) => {
    if (!isControlled) setInternal(newValue);
    onChange?.(newValue);
  };
  
  return <input value={current} onChange={handleChange} />;
}
```

## React Query Integration

### Query Hooks

Create custom hooks that encapsulate queries:

```typescript
export function useUserList() {
  return useQuery({
    queryKey: ['users', 'list'],
    queryFn: fetchUsers,
  });
}
```

### Query Key Factories

Organize keys consistently:

```typescript
const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  detail: (id: string) => [...userKeys.all, 'detail', id] as const,
};
```

### Composition with Queries

Separate data fetching from presentation:

```typescript
function UserList() {
  const { data, isLoading, error } = useUserList();
  
  if (isLoading) return <Spinner />;
  if (error) return <Error error={error} />;
  
  return (
    <List>
      {data.map(user => <UserItem key={user.id} user={user} />)}
    </List>
  );
}
```

### Mutations with Optimistic Updates

Use immutable patterns for optimistic updates:

```typescript
const mutation = useMutation({
  mutationFn: updateUser,
  onMutate: async (updated) => {
    await queryClient.cancelQueries({ queryKey: userKeys.detail(updated.id) });
    const previous = queryClient.getQueryData(userKeys.detail(updated.id));
    queryClient.setQueryData(userKeys.detail(updated.id), updated);
    return { previous };
  },
  onError: (err, updated, context) => {
    queryClient.setQueryData(userKeys.detail(updated.id), context?.previous);
  },
  onSettled: (data) => {
    queryClient.invalidateQueries({ queryKey: userKeys.detail(data.id) });
  },
});
```

## Pure Component Requirements

### Idempotency

Same props must always produce same output:

```typescript
// Pure - always renders same output for same input
function UserCard({ user }: { user: User }) {
  return <div>{user.name}</div>;
}

// Impure - side effects in render
function ImpureCard({ user }: { user: User }) {
  trackEvent('card_viewed'); // DON'T DO THIS
  return <div>{user.name}</div>;
}

// Fixed - side effects in useEffect
function PureCard({ user }: { user: User }) {
  useEffect(() => {
    trackEvent('card_viewed');
  }, [user.id]);
  
  return <div>{user.name}</div>;
}
```

### Avoid Mutations

Never mutate props or state directly:

```typescript
// Bad - mutates prop
function BadList({ items }: { items: Item[] }) {
  items.sort(); // Mutates!
  return <ul>{items.map(item => <li>{item.name}</li>)}</ul>;
}

// Good - creates new array
function GoodList({ items }: { items: Item[] }) {
  const sorted = [...items].sort();
  return <ul>{sorted.map(item => <li>{item.name}</li>)}</ul>;
}
```

## TypeScript Typing

### Props Interfaces

Use clear, specific types:

```typescript
interface SelectProps {
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  children: React.ReactNode;
  disabled?: boolean;
}
```

### Context Typing

Always type context values:

```typescript
interface ContextValue {
  state: State;
  actions: Actions;
}

const Context = createContext<ContextValue | null>(null);
```

### Generic Components

Support generic types when needed:

```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
}

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return (
    <ul>
      {items.map(item => (
        <li key={keyExtractor(item)}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}
```

## Detailed References

For comprehensive patterns and examples:

- **Compositional patterns** - See `references/compositional-patterns.md` for headless UI patterns, compound components, render props, slots, and purity guidelines
- **React Query integration** - See `references/react-query-patterns.md` for query organization, mutations, infinite queries, and error handling
- **Complete example** - See `assets/select-component-template.tsx` for a fully-implemented compositional select component demonstrating all patterns

## Common Patterns

### Data List with Infinite Scroll

```typescript
function UserList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['users'],
    queryFn: ({ pageParam = 0 }) => fetchUsers(pageParam),
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    initialPageParam: 0,
  });

  return (
    <>
      {data?.pages.flatMap(page => page.users).map(user => (
        <UserCard key={user.id} user={user} />
      ))}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          Load More
        </button>
      )}
    </>
  );
}
```

### Dependent Queries

```typescript
function UserProfile({ userId }: { userId: string }) {
  const { data: user } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  });

  const { data: posts } = useQuery({
    queryKey: ['posts', userId],
    queryFn: () => fetchPosts(userId),
    enabled: !!user, // Only fetch when user exists
  });

  if (!user) return <Spinner />;

  return (
    <div>
      <h1>{user.name}</h1>
      {posts?.map(post => <PostCard key={post.id} post={post} />)}
    </div>
  );
}
```

### Error Boundaries

Always wrap components with error boundaries:

```typescript
<ErrorBoundary fallback={<ErrorFallback />}>
  <Suspense fallback={<LoadingSpinner />}>
    <ComponentThatMightFail />
  </Suspense>
</ErrorBoundary>
```

## Checklist

Before considering a component complete:

- [ ] Separated UI state from server state
- [ ] Extracted reusable logic to hooks
- [ ] Components are pure (no side effects in render)
- [ ] No prop mutations or direct state mutations
- [ ] Proper TypeScript types throughout
- [ ] Supports both controlled and uncontrolled (where applicable)
- [ ] React Query queries use consistent key factories
- [ ] Mutations handle optimistic updates correctly
- [ ] Error boundaries and suspense boundaries in place
- [ ] Accessibility attributes (ARIA) included