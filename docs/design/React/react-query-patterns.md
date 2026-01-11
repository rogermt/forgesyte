# React Query Integration Patterns

## Core Principles

React Query handles server state while compositional components manage UI state. Keep these concerns separate.

## Query Organization

### Custom Hooks Pattern

Create custom hooks that encapsulate query logic:

```typescript
// hooks/useUserData.ts
export function useUserData(userId: string) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

### Query Key Factories

Organize query keys consistently:

```typescript
// queries/keys.ts
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters: string) => [...userKeys.lists(), { filters }] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
};
```

## Composition with Headless Components

### Separate Data from Presentation

```typescript
// Headless data component
function useUserList() {
  const { data, isLoading, error } = useQuery({
    queryKey: userKeys.lists(),
    queryFn: fetchUsers,
  });

  return { users: data, isLoading, error };
}

// Compositional UI component
function UserList({ children }: { children: (state: ReturnType<typeof useUserList>) => React.ReactNode }) {
  const state = useUserList();
  return <>{children(state)}</>;
}

// Usage
<UserList>
  {({ users, isLoading, error }) => (
    isLoading ? <Spinner /> :
    error ? <Error error={error} /> :
    <ul>{users?.map(user => <UserItem key={user.id} user={user} />)}</ul>
  )}
</UserList>
```

## Mutations with Optimistic Updates

### Immutable Update Pattern

```typescript
function useUpdateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (user: User) => updateUser(user),
    onMutate: async (updatedUser) => {
      await queryClient.cancelQueries({ queryKey: userKeys.detail(updatedUser.id) });
      
      const previous = queryClient.getQueryData(userKeys.detail(updatedUser.id));
      
      queryClient.setQueryData(userKeys.detail(updatedUser.id), updatedUser);
      
      return { previous };
    },
    onError: (err, updatedUser, context) => {
      queryClient.setQueryData(
        userKeys.detail(updatedUser.id),
        context?.previous
      );
    },
    onSettled: (data) => {
      queryClient.invalidateQueries({ queryKey: userKeys.detail(data.id) });
    },
  });
}
```

## Infinite Queries with Composition

```typescript
function useInfiniteUserList() {
  return useInfiniteQuery({
    queryKey: userKeys.lists(),
    queryFn: ({ pageParam = 0 }) => fetchUsers(pageParam),
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    initialPageParam: 0,
  });
}

// Compositional pattern
function InfiniteList<T>({ 
  children, 
  useInfiniteData 
}: { 
  children: (item: T) => React.ReactNode,
  useInfiniteData: () => UseInfiniteQueryResult<{ data: T[] }>
}) {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteData();
  
  return (
    <>
      {data?.pages.flatMap(page => page.data).map(children)}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          Load More
        </button>
      )}
    </>
  );
}
```

## Dependent Queries

```typescript
function useUserProfile(userId: string) {
  const { data: user } = useQuery({
    queryKey: userKeys.detail(userId),
    queryFn: () => fetchUser(userId),
  });

  const { data: posts } = useQuery({
    queryKey: ['posts', userId],
    queryFn: () => fetchUserPosts(userId),
    enabled: !!user, // Only run when user exists
  });

  return { user, posts };
}
```

## Error Boundaries

Always wrap components using queries with error boundaries:

```typescript
function QueryErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      fallbackRender={({ error, resetErrorBoundary }) => (
        <div>
          <h2>Something went wrong</h2>
          <pre>{error.message}</pre>
          <button onClick={resetErrorBoundary}>Try again</button>
        </div>
      )}
    >
      <Suspense fallback={<LoadingSpinner />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}
```
