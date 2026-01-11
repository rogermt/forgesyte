import { 
  createContext, 
  useContext, 
  useState, 
  useCallback, 
  useMemo,
  useEffect,
  useReducer
} from 'react';

/**
 * Example: Compositional Select Component
 * 
 * Demonstrates:
 * - Compound components pattern
 * - Headless logic separation
 * - Pure, idempotent rendering
 * - Proper TypeScript typing
 * - Accessibility
 */

// ============================================================================
// Types
// ============================================================================

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectContextValue {
  value: string | null;
  onChange: (value: string) => void;
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  options: SelectOption[];
  highlightedIndex: number;
  setHighlightedIndex: (index: number) => void;
}

// ============================================================================
// Context
// ============================================================================

const SelectContext = createContext<SelectContextValue | null>(null);

function useSelectContext() {
  const context = useContext(SelectContext);
  if (!context) {
    throw new Error('Select compound components must be used within Select');
  }
  return context;
}

// ============================================================================
// Hooks (Headless Logic)
// ============================================================================

interface UseSelectProps {
  value?: string | null;
  defaultValue?: string | null;
  onChange?: (value: string) => void;
  options: SelectOption[];
}

function useSelect({ 
  value: controlledValue, 
  defaultValue, 
  onChange,
  options 
}: UseSelectProps) {
  const [internalValue, setInternalValue] = useState<string | null>(
    defaultValue ?? null
  );
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;

  const handleChange = useCallback((newValue: string) => {
    if (!isControlled) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
    setIsOpen(false);
  }, [isControlled, onChange]);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => {
    setIsOpen(false);
    setHighlightedIndex(0);
  }, []);
  const toggle = useCallback(() => setIsOpen(prev => !prev), []);

  // Reset highlighted index when opening
  useEffect(() => {
    if (isOpen) {
      const selectedIndex = options.findIndex(opt => opt.value === value);
      setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : 0);
    }
  }, [isOpen, value, options]);

  return {
    value,
    onChange: handleChange,
    isOpen,
    open,
    close,
    toggle,
    options,
    highlightedIndex,
    setHighlightedIndex,
  };
}

// ============================================================================
// Root Component
// ============================================================================

interface SelectProps extends Omit<UseSelectProps, 'options'> {
  children: React.ReactNode;
  options: SelectOption[];
}

export function Select({ children, ...props }: SelectProps) {
  const state = useSelect(props);

  return (
    <SelectContext.Provider value={state}>
      <div className="select-container">
        {children}
      </div>
    </SelectContext.Provider>
  );
}

// ============================================================================
// Compound Components
// ============================================================================

interface SelectTriggerProps {
  children?: React.ReactNode;
  placeholder?: string;
}

function SelectTrigger({ children, placeholder = 'Select...' }: SelectTriggerProps) {
  const { value, options, isOpen, toggle } = useSelectContext();
  
  const selectedOption = useMemo(
    () => options.find(opt => opt.value === value),
    [options, value]
  );

  return (
    <button
      type="button"
      onClick={toggle}
      aria-haspopup="listbox"
      aria-expanded={isOpen}
      className="select-trigger"
    >
      {children ?? (
        <span>
          {selectedOption?.label ?? placeholder}
        </span>
      )}
    </button>
  );
}

interface SelectContentProps {
  children: React.ReactNode;
}

function SelectContent({ children }: SelectContentProps) {
  const { isOpen, close } = useSelectContext();

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.select-container')) {
        close();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, close]);

  if (!isOpen) return null;

  return (
    <div className="select-content" role="listbox">
      {children}
    </div>
  );
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  disabled?: boolean;
}

function SelectItem({ value: itemValue, children, disabled }: SelectItemProps) {
  const { 
    value, 
    onChange, 
    options,
    highlightedIndex,
    setHighlightedIndex 
  } = useSelectContext();

  const index = useMemo(
    () => options.findIndex(opt => opt.value === itemValue),
    [options, itemValue]
  );

  const isSelected = value === itemValue;
  const isHighlighted = highlightedIndex === index;

  const handleClick = useCallback(() => {
    if (!disabled) {
      onChange(itemValue);
    }
  }, [disabled, onChange, itemValue]);

  const handleMouseEnter = useCallback(() => {
    if (!disabled) {
      setHighlightedIndex(index);
    }
  }, [disabled, setHighlightedIndex, index]);

  return (
    <div
      role="option"
      aria-selected={isSelected}
      aria-disabled={disabled}
      className={`select-item ${isSelected ? 'selected' : ''} ${isHighlighted ? 'highlighted' : ''} ${disabled ? 'disabled' : ''}`}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
    >
      {children}
    </div>
  );
}

// ============================================================================
// Attach Compound Components
// ============================================================================

Select.Trigger = SelectTrigger;
Select.Content = SelectContent;
Select.Item = SelectItem;

// ============================================================================
// Usage Example
// ============================================================================

export function ExampleUsage() {
  const [value, setValue] = useState<string | null>(null);

  const options = [
    { value: 'apple', label: 'Apple' },
    { value: 'banana', label: 'Banana' },
    { value: 'orange', label: 'Orange' },
    { value: 'grape', label: 'Grape', disabled: true },
  ];

  return (
    <div>
      <h2>Controlled Select</h2>
      <Select 
        value={value} 
        onChange={setValue}
        options={options}
      >
        <Select.Trigger />
        <Select.Content>
          {options.map(option => (
            <Select.Item 
              key={option.value} 
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </Select.Item>
          ))}
        </Select.Content>
      </Select>

      <h2>Uncontrolled Select with Custom Trigger</h2>
      <Select 
        defaultValue="banana"
        onChange={(val) => console.log('Selected:', val)}
        options={options}
      >
        <Select.Trigger>
          <div className="custom-trigger">
            Custom Trigger UI
          </div>
        </Select.Trigger>
        <Select.Content>
          {options.map(option => (
            <Select.Item 
              key={option.value} 
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </Select.Item>
          ))}
        </Select.Content>
      </Select>
    </div>
  );
}
