# Compositional Component Patterns

## Core Principles

### Composition over Props

Build components that combine through composition rather than complex prop APIs:

**Bad:**
```typescript
<DataTable 
  data={data} 
  showHeader={true} 
  sortable={true} 
  filterable={true}
  customRenderer={(row) => <CustomRow data={row} />}
  headerStyle={{}}
  rowStyle={{}}
/>
```

**Good:**
```typescript
<Table>
  <TableHeader>
    <TableRow>
      <TableHeaderCell sortable>Name</TableHeaderCell>
      <TableHeaderCell>Email</TableHeaderCell>
    </TableRow>
  </TableHeader>
  <TableBody>
    {data.map(row => (
      <TableRow key={row.id}>
        <TableCell>{row.name}</TableCell>
        <TableCell>{row.email}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

## Headless Component Pattern

### Separate Logic from Presentation

```typescript
// Headless hook (logic only)
function useDisclosure(initialOpen = false) {
  const [isOpen, setIsOpen] = useState(initialOpen);
  
  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen(prev => !prev), []);
  
  return { isOpen, open, close, toggle };
}

// Render props pattern
function Disclosure({ 
  children,
  defaultOpen = false 
}: { 
  children: (state: ReturnType<typeof useDisclosure>) => React.ReactNode;
  defaultOpen?: boolean;
}) {
  const disclosure = useDisclosure(defaultOpen);
  return <>{children(disclosure)}</>;
}

// Usage
<Disclosure>
  {({ isOpen, toggle }) => (
    <>
      <button onClick={toggle}>Toggle</button>
      {isOpen && <div>Content</div>}
    </>
  )}
</Disclosure>
```

## Compound Components Pattern

Components that work together through shared context:

```typescript
interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabs() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tabs compounds must be used within Tabs');
  }
  return context;
}

function Tabs({ 
  children, 
  defaultTab 
}: { 
  children: React.ReactNode; 
  defaultTab: string;
}) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </TabsContext.Provider>
  );
}

function TabList({ children }: { children: React.ReactNode }) {
  return <div role="tablist">{children}</div>;
}

function Tab({ 
  value, 
  children 
}: { 
  value: string; 
  children: React.ReactNode;
}) {
  const { activeTab, setActiveTab } = useTabs();
  const isActive = activeTab === value;
  
  return (
    <button
      role="tab"
      aria-selected={isActive}
      onClick={() => setActiveTab(value)}
    >
      {children}
    </button>
  );
}

function TabPanel({ 
  value, 
  children 
}: { 
  value: string; 
  children: React.ReactNode;
}) {
  const { activeTab } = useTabs();
  
  if (activeTab !== value) return null;
  
  return <div role="tabpanel">{children}</div>;
}

// Export as namespace
Tabs.List = TabList;
Tabs.Tab = Tab;
Tabs.Panel = TabPanel;

// Usage
<Tabs defaultTab="overview">
  <Tabs.List>
    <Tabs.Tab value="overview">Overview</Tabs.Tab>
    <Tabs.Tab value="details">Details</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel value="overview">Overview content</Tabs.Panel>
  <Tabs.Panel value="details">Details content</Tabs.Panel>
</Tabs>
```

## State Reducer Pattern

Allow consumers to control state updates:

```typescript
type Action = 
  | { type: 'INCREMENT' }
  | { type: 'DECREMENT' }
  | { type: 'RESET'; payload: number };

interface State {
  count: number;
}

function defaultReducer(state: State, action: Action): State {
  switch (action.type) {
    case 'INCREMENT':
      return { count: state.count + 1 };
    case 'DECREMENT':
      return { count: state.count - 1 };
    case 'RESET':
      return { count: action.payload };
    default:
      return state;
  }
}

function Counter({ 
  initialCount = 0,
  reducer = defaultReducer,
  children 
}: {
  initialCount?: number;
  reducer?: typeof defaultReducer;
  children: (state: State, actions: {
    increment: () => void;
    decrement: () => void;
    reset: () => void;
  }) => React.ReactNode;
}) {
  const [state, dispatch] = useReducer(reducer, { count: initialCount });
  
  const actions = useMemo(() => ({
    increment: () => dispatch({ type: 'INCREMENT' }),
    decrement: () => dispatch({ type: 'DECREMENT' }),
    reset: () => dispatch({ type: 'RESET', payload: initialCount }),
  }), [initialCount]);
  
  return <>{children(state, actions)}</>;
}
```

## Slot Pattern

Flexible content placement:

```typescript
interface CardProps {
  header?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
}

function Card({ header, footer, children }: CardProps) {
  return (
    <div className="card">
      {header && <div className="card-header">{header}</div>}
      <div className="card-body">{children}</div>
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  );
}

// Usage
<Card 
  header={<h2>Title</h2>}
  footer={<button>Action</button>}
>
  <p>Content goes here</p>
</Card>
```

## Pure Component Guidelines

### Idempotency

Same input always produces same output:

```typescript
// Pure - idempotent
function UserCard({ user }: { user: User }) {
  return (
    <div>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
}

// Impure - not idempotent (side effect in render)
function ImpureUserCard({ user }: { user: User }) {
  logAnalytics('card_viewed', user.id); // Side effect!
  return (
    <div>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
}

// Fixed - side effects in useEffect
function PureUserCard({ user }: { user: User }) {
  useEffect(() => {
    logAnalytics('card_viewed', user.id);
  }, [user.id]);
  
  return (
    <div>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
}
```

### Avoid Direct Mutations

```typescript
// Bad - mutates prop
function BadList({ items }: { items: Item[] }) {
  items.sort(); // Mutates the original array!
  return <ul>{items.map(item => <li>{item.name}</li>)}</ul>;
}

// Good - creates new array
function GoodList({ items }: { items: Item[] }) {
  const sortedItems = [...items].sort();
  return <ul>{sortedItems.map(item => <li>{item.name}</li>)}</ul>;
}
```

## Controlled vs Uncontrolled Pattern

Support both patterns for flexibility:

```typescript
interface InputProps {
  value?: string; // Controlled
  defaultValue?: string; // Uncontrolled
  onChange?: (value: string) => void;
}

function Input({ value, defaultValue, onChange }: InputProps) {
  const [internalValue, setInternalValue] = useState(defaultValue ?? '');
  
  const isControlled = value !== undefined;
  const currentValue = isControlled ? value : internalValue;
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    if (!isControlled) {
      setInternalValue(newValue);
    }
    
    onChange?.(newValue);
  };
  
  return <input value={currentValue} onChange={handleChange} />;
}

// Controlled usage
<Input value={value} onChange={setValue} />

// Uncontrolled usage
<Input defaultValue="initial" onChange={(val) => console.log(val)} />
```
