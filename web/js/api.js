export async function fetchTrends(entity, params = {}) {
    const query = new URLSearchParams({ entity, ...params }).toString();
    const response = await fetch(`/api/trends?${query}`);
    return response.json();
}

export async function fetchPhrases(entity, params = {}) {
    const query = new URLSearchParams({ entity, ...params }).toString();
    const response = await fetch(`/api/phrases?${query}`);
    return response.json();
}

export async function fetchNetwork(entity, params = {}) {
    const searchParams = new URLSearchParams({ entity });
    Object.keys(params).forEach(key => {
        if (Array.isArray(params[key])) {
            params[key].forEach(val => searchParams.append(key, val));
        } else {
            searchParams.append(key, params[key]);
        }
    });
    const response = await fetch(`/api/network?${searchParams.toString()}`);
    return response.json();
}
