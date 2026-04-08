import { api } from './api';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export const communityApi = {
  list: () => api.get('/communities/'),
  get: (slug) => api.get(`/communities/${slug}`),
  myCommunities: () => api.get('/communities/my-communities'),
  join: (slug) => api.post(`/community/${slug}/join`),
  leave: (slug) => api.post(`/community/${slug}/leave`),
  requestJoin: (slug, data) => api.post(`/communities/${slug}/request-join`, data),
  membershipStatus: (slug) => api.get(`/communities/${slug}/membership-status`),
  members: (slug) => api.get(`/community/${slug}/members`),
};

export const discussionApi = {
  categories: (slug) => api.get(`/communities/${slug}/categories`),
  threads: (slug, params) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return api.get(`/communities/${slug}/threads${qs}`);
  },
  thread: (slug, threadId) => api.get(`/communities/${slug}/threads/${threadId}`),
  createThread: (slug, data) => api.post(`/communities/${slug}/threads`, data),
  updateThread: (slug, threadId, data) => api.patch(`/communities/${slug}/threads/${threadId}`, data),
  deleteThread: (slug, threadId) => api.del(`/communities/${slug}/threads/${threadId}`),
  posts: (slug, threadId) => api.get(`/communities/${slug}/threads/${threadId}/posts`),
  createPost: (slug, threadId, data) => api.post(`/communities/${slug}/threads/${threadId}/posts`, data),
  updatePost: (slug, threadId, postId, data) => api.patch(`/communities/${slug}/threads/${threadId}/posts/${postId}`, data),
  deletePost: (slug, threadId, postId) => api.del(`/communities/${slug}/threads/${threadId}/posts/${postId}`),
};

export const eventApi = {
  list: (slug) => api.get(`/communities/${slug}/events`),
  get: (slug, eventId) => api.get(`/communities/${slug}/events/${eventId}`),
};

export const managerApi = {
  myCommunities: () => api.get('/manager/my-communities'),
  community: (slug) => api.get(`/manager/communities/${slug}`),
  updateCommunity: (slug, data) => api.patch(`/manager/communities/${slug}`, data),
  createCategory: (slug, data) => api.post(`/manager/communities/${slug}/categories`, data),
  approveThread: (slug, threadId) => api.post(`/manager/communities/${slug}/threads/${threadId}/approve`),
  rejectThread: (slug, threadId) => api.post(`/manager/communities/${slug}/threads/${threadId}/reject`),
  createEvent: (slug, data) => api.post(`/manager/communities/${slug}/events`, data),
  managerEvents: (slug) => api.get(`/manager/communities/${slug}/events`),
  updateEvent: (slug, eventId, data) => api.patch(`/manager/communities/${slug}/events/${eventId}`, data),
  deleteEvent: (slug, eventId) => api.del(`/manager/communities/${slug}/events/${eventId}`),
  uploadMedia: (slug, eventId, formData) => api.upload(`/manager/communities/${slug}/events/${eventId}/upload-media`, formData),
  deleteMedia: (slug, eventId, mediaId) => api.del(`/manager/communities/${slug}/events/${eventId}/media/${mediaId}`),
  joinRequests: (slug) => api.get(`/manager/communities/${slug}/join-requests`),
  approveJoinRequest: (slug, requestId) => api.post(`/manager/communities/${slug}/join-requests/${requestId}/approve`),
  rejectJoinRequest: (slug, requestId) => api.post(`/manager/communities/${slug}/join-requests/${requestId}/reject`),
  banMember: (slug, userId) => api.post(`/manager/communities/${slug}/members/${userId}/ban`),
  restoreMember: (slug, userId) => api.post(`/manager/communities/${slug}/members/${userId}/restore`),
  sendNotification: (slug, data) => api.post(`/manager/communities/${slug}/notifications/send-event`, data),
};

export const profileApi = {
  get: () => api.get('/profile'),
  update: (data) => api.patch('/profile', data),
};

export const searchApi = {
  search: (slug, query) => api.get(`/communities/${slug}/search?q=${encodeURIComponent(query)}`),
};

export const authApi = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (email, name, password) => api.post('/auth/register', { email, name, password }),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout', {}),
  session: (sessionId) => api.post(`/auth/session?session_id=${sessionId}`, {}),
};

export { API };
