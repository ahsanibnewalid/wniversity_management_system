import React, { useEffect, useState } from "react";
import {
  AppState,
  ActivityIndicator,
  Alert,
  BackHandler,
  KeyboardAvoidingView,
  Linking,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  StatusBar,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { NavigationBar } from "expo-navigation-bar";

const API =
  process.env.EXPO_PUBLIC_API_URL || "http://localhost:5000/api/v1";

const adminTabs = [
  ["Overview", "overview"],
  ["Institution", "institution"],
  ["Members", "members"],
  ["Departments", "departments"],
  ["Sessions", "sessions"],
  ["Groups", "groups"],
  ["Requests", "requests"],
  ["Faculties", "faculties"],
  ["Programs", "programs"],
  ["Courses", "adminCourses"],
  ["Events", "adminEvents"],
  ["Clubs", "adminClubs"],
  ["Services", "adminServices"],
  ["Fees", "adminFees"],
];

const featureGroups = [
  {
    title: "Study",
    description: "Your courses, assessments, and academic progress.",
    items: [
      ["Course Registration", "Browse and enroll in open courses"],
      ["Assignments", "Review deadlines and submit your work"],
      ["Attendance", "Check your attendance record"],
      ["Results", "View grades and your transcript summary"],
      ["Timetable", "See your weekly class schedule"],
      ["Calendar", "Keep track of academic dates"],
    ],
  },
  {
    title: "Campus",
    description: "People, services, and activities around your university.",
    items: [
      ["Announcements", "Updates from your institution"],
      ["Groups", "Join a group and open its community feed"],
      ["Events", "Discover events and register"],
      ["Clubs", "Find clubs and join"],
      ["Documents", "Open shared university documents"],
      ["Services", "Create and track service requests"],
      ["Certificates", "View certificates issued to you"],
      ["Campus", "Campus services and contact information"],
      ["Library", "Browse the library collection"],
      ["My library loans", "Check and return borrowed books"],
      ["Hostel", "View rooms and submit an application"],
      ["Lost & Found", "Browse or report a lost item"],
      ["Fees", "Review your fee balance and due dates"],
      ["Bus Routes", "View campus transportation schedules"],
      ["Emergency Contacts", "Find university emergency contacts"],
      ["Cafeteria Menu", "Check available campus food options"],
      ["Student Requests", "Track university service requests"],
    ],
  },
  {
    title: "Account",
    description: "Manage your profile and conversations.",
    items: [
      ["Messages", "Open conversations with university members"],
      ["Notifications", "Read your latest account updates"],
      ["Search", "Find people, courses, and departments"],
      ["My Profile", "Review and update your profile"],
      ["My University", "Join, create, or switch universities"],
    ],
  },
];

const primaryTabs = [
  ["Home", "⌂"],
  ["Courses", "▤"],
  ["Campus", "⌖"],
  ["More", "•••"],
];

const screenTitles = {
  "Course Registration": "Course registration",
  "Lost & Found": "Lost & found",
  "My library loans": "My library loans",
  "My Profile": "My profile",
  "Member Profile": "Member profile",
  "My University": "My university",
};

const adminPaths = {
  overview: "/admin/overview",
  institution: "/admin",
  members: "/admin/members",
  departments: "/admin/departments",
  sessions: "/admin/sessions",
  groups: "/admin/groups",
  requests: "/admin/requests",
  faculties: "/admin/faculties",
  programs: "/admin/programs",
  adminCourses: "/admin/courses",
  adminEvents: "/admin/events",
  adminClubs: "/admin/clubs",
  adminServices: "/admin/service-requests",
  adminFees: "/admin/fees",
};

async function request(path, token, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const text = await response.text();
  let result = {};
  if (text) {
    try {
      result = JSON.parse(text);
    } catch {
      result = {};
    }
  }
  if (!response.ok) {
    throw new Error(
      result.error || result.message || `Request failed (${response.status})`,
    );
  }
  return result;
}

function jsonOptions(method, body) {
  return { method, body: JSON.stringify(body) };
}

function titleFor(screen) {
  return (
    adminTabs.find(([, key]) => key === screen)?.[0] ||
    screenTitles[screen] ||
    screen
  );
}

function screenItems(screen, data) {
  if (screen === "Results") return data?.results || [];
  return data?.items || [];
}

function itemTitle(item) {
  return (
    item.course_title ||
    item.title ||
    item.name ||
    (item.room_number ? `Room ${item.room_number}` : null) ||
    (item.course_id ? `Course #${item.course_id}` : null) ||
    item.request_type ||
    item.question ||
    item.body ||
    item.kind ||
    `Item ${item.id || ""}`
  );
}

function itemDetails(screen, item) {
  const fields = [];
  if (item.course_code) fields.push(item.course_code);
  if (item.section) fields.push(`Section ${item.section}`);
  if (item.credits != null) fields.push(`${item.credits} credits`);
  if (item.event_type) fields.push(item.event_type);
  if (item.starts_at) fields.push(formatDate(item.starts_at));
  if (item.location) fields.push(item.location);
  if (item.amount != null) fields.push(`Amount: ${item.amount}`);
  if (item.due_date) fields.push(`Due ${formatDate(item.due_date)}`);
  if (item.status) fields.push(item.status);
  if (item.grade) fields.push(`Grade ${item.grade}`);
  if (item.grade_point != null) fields.push(`${item.grade_point} points`);
  if (item.weekday != null) {
    fields.push(
      ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][item.weekday] ||
        `Day ${item.weekday}`,
    );
  }
  if (item.start_time && item.end_time)
    fields.push(`${item.start_time}–${item.end_time}`);
  if (item.available_copies != null)
    fields.push(`${item.available_copies} available`);
  if (item.tracking_no) fields.push(`Tracking ${item.tracking_no}`);
  if (item.audience && screen === "Announcements")
    fields.push(`For ${item.audience}`);
  if (item.category) fields.push(item.category);
  if (item.code && !item.course_code) fields.push(item.code);
  if (item.subtitle) fields.push(item.subtitle);
  return [...new Set(fields)].join("  ·  ");
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString();
}

export default function App() {
  const [token, setToken] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);
  const [registerMode, setRegisterMode] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");

  const [screen, setScreen] = useState("Home");
  const navigationHistory = React.useRef([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [error, setError] = useState("");
  const [institution, setInstitution] = useState(null);
  const [platformAdmin, setPlatformAdmin] = useState(false);
  const [admins, setAdmins] = useState([]);
  const [userId, setUserId] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [viewUser, setViewUser] = useState(null);
  const [viewMessages, setViewMessages] = useState([]);
  const [profile, setProfile] = useState(null);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState({});
  const [selectedAssignment, setSelectedAssignment] = useState(null);

  useEffect(() => {
    AsyncStorage.getItem("token")
      .then(setToken)
      .catch((storageError) => setError(storageError.message))
      .finally(() => setAuthReady(true));
  }, []);

  useEffect(() => {
    if (Platform.OS !== "android") return undefined;

    function applySystemBars() {
      NavigationBar.setStyle("dark");
      NavigationBar.setHidden(true);
    }

    applySystemBars();
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "active") applySystemBars();
    });
    return () => subscription.remove();
  }, []);

  useEffect(() => {
    const subscription = BackHandler.addEventListener(
      "hardwareBackPress",
      () => {
        if (!token) {
          if (registerMode) {
            setRegisterMode(false);
            setError("");
          }
          return true;
        }

        const previous = navigationHistory.current.pop();
        if (previous) {
          setScreen(previous.screen);
          setData(previous.data);
          setSelectedGroup(previous.selectedGroup);
          setViewUser(previous.viewUser);
          setViewMessages(previous.viewMessages);
          setProfile(previous.profile);
          setQuery(previous.query);
          setForm(previous.form);
          setSelectedAssignment(previous.selectedAssignment);
          setInstitution(previous.institution);
          setError("");
          return true;
        }

        if (screen !== "Home") {
          load("Home", undefined, "reset");
          return true;
        }

        return true;
      },
    );
    return () => subscription.remove();
  }, [token, registerMode, screen]);

  function navigateToScreen(nextScreen, mode = "push") {
    if (mode === "reset") {
      navigationHistory.current = [];
    } else if (screen !== nextScreen) {
      navigationHistory.current.push({
        screen,
        data,
        selectedGroup,
        viewUser,
        viewMessages,
        profile,
        query,
        form,
        selectedAssignment,
        institution,
      });
      if (navigationHistory.current.length > 30) {
        navigationHistory.current.shift();
      }
    }
    setScreen(nextScreen);
  }

  useEffect(() => {
    if (!token) return undefined;
    let active = true;

    async function bootstrap() {
      setLoading(true);
      setError("");
      try {
        const [membershipData, currentUser] = await Promise.all([
          request("/my/institutions", token),
          request("/auth/me", token),
        ]);
        const firstInstitution = membershipData.items?.[0] || null;
        if (active) {
          setInstitution(firstInstitution);
          setUserId(currentUser.id);
          setPlatformAdmin(Boolean(currentUser.platform_admin));
        }
        const dashboard = await request("/dashboard", token);
        if (active) {
          setData(dashboard);
          navigationHistory.current = [];
          setScreen("Home");
        }
      } catch (loadError) {
        if (active) setError(loadError.message);
      } finally {
        if (active) setLoading(false);
      }
    }

    bootstrap();
    return () => {
      active = false;
    };
  }, [token]);

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function authenticate() {
    if (!email.trim() || !password) {
      setError("Enter your email and password to continue.");
      return;
    }
    if (registerMode && (!fullName.trim() || !username.trim() || password.length < 8)) {
      setError("Enter your name, username, email, and a password of at least 8 characters.");
      return;
    }

    setAuthBusy(true);
    setError("");
    try {
      if (registerMode) {
        await request(
          "/auth/register",
          null,
          jsonOptions("POST", {
            full_name: fullName.trim(),
            username: username.trim(),
            email: email.trim(),
            password,
          }),
        );
      }
      const result = await request(
        "/auth/login",
        null,
        jsonOptions("POST", { email: email.trim(), password }),
      );
      await AsyncStorage.setItem("token", result.access_token);
      setToken(result.access_token);
      setRegisterMode(false);
      navigationHistory.current = [];
    } catch (authError) {
      setError(authError.message);
    } finally {
      setAuthBusy(false);
    }
  }

  async function logout() {
    try {
      await AsyncStorage.removeItem("token");
      navigationHistory.current = [];
      setToken(null);
      setScreen("Home");
      setData(null);
      setInstitution(null);
      setPlatformAdmin(false);
      setAdmins([]);
      setUserId(null);
      setViewUser(null);
      setError("");
    } catch (storageError) {
      setError(storageError.message);
    }
  }

  async function loadAdmin(
    section,
    institutionId = institution?.id,
    navigationMode = "push",
  ) {
    if (!institutionId) {
      setError("Choose an institution before opening its admin tools.");
      return;
    }
    const path = adminPaths[section];
    if (!path) {
      setError("This admin section is not available.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await request(
        `/institutions/${institutionId}${path}`,
        token,
      );
      setData(result);
      navigateToScreen(section, navigationMode);
      if (result.institution) setInstitution(result.institution);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function load(
    type,
    institutionId = institution?.id,
    navigationMode = "push",
  ) {
    if (type === "More") {
      navigateToScreen("More", navigationMode);
      setError("");
      return;
    }
    if (type === "Search") {
      navigateToScreen("Search", navigationMode);
      setData({ items: [] });
      setError("");
      return;
    }
    if (type === "Community") {
      if (selectedGroup) {
        await openGroup(selectedGroup);
      } else {
        await load("Groups", institutionId);
      }
      return;
    }
    if (type === "Admin") {
      setLoading(true);
      setError("");
      try {
        const result = await request("/admin/institutions", token);
        setAdmins(result.items || []);
        setData(result);
        navigateToScreen("Admin", navigationMode);
        if (result.items?.length && !institution) {
          setInstitution(result.items[0]);
        }
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
      return;
    }
    if (adminPaths[type]) {
      await loadAdmin(type, institutionId, navigationMode);
      return;
    }
    if (type === "Platform Admin" && !platformAdmin) {
      setError("Platform administrator access is required.");
      return;
    }
    if (type === "Teaching" && institution?.role !== "teacher") {
      setError("An active teacher membership is required.");
      return;
    }

    const routes = {
      Home: "/dashboard",
      Courses: "/me/enrollments",
      "Course Registration": "/me/course-registration",
      Assignments: "/me/enrollments",
      Attendance: "/me/attendance",
      Results: "/me/transcript",
      Timetable: "/me/timetable",
      Calendar: "/academic-calendar",
      Announcements: institutionId
        ? `/institutions/${institutionId}/announcements`
        : null,
      Groups: institutionId ? `/institutions/${institutionId}/groups` : null,
      Events: "/events",
      Clubs: "/clubs",
      Documents: "/documents",
      Services: "/service-requests",
      Certificates: "/certificates",
      Campus: "/campus-services",
      Library: institutionId ? `/library/${institutionId}/items` : null,
      "My library loans": "/library/my-loans",
      Hostel: institutionId ? `/hostel/${institutionId}/rooms` : null,
      "Lost & Found": "/lost-found",
      Fees: "/fees",
      Messages: "/messages",
      Notifications: "/notifications",
      "My Profile": "/profile",
      "My University": "/my/institutions",
      "Platform Admin": "/platform/admin/overview",
      Teaching: "/teacher/dashboard",
      "Student Requests": "/service-requests/advanced",
      "Bus Routes": institutionId ? `/bus-routes/${institutionId}` : null,
      "Emergency Contacts": institutionId
        ? `/emergency-contacts/${institutionId}`
        : null,
      "Cafeteria Menu": institutionId ? `/cafeteria/${institutionId}` : null,
    };

    if (!routes[type]) {
      setError("This section is not available.");
      return;
    }
    if (routes[type] === null) {
      setError("Join an institution to use this section.");
      return;
    }
    setLoading(true);
    setError("");
    setSelectedAssignment(null);
    setForm({});
    try {
      let result = await request(routes[type], token);
      if (type === "Assignments") {
        const assignments = await Promise.all(
          (result.items || []).map(async (enrollment) => {
            const courseAssignments = await request(
              `/offerings/${enrollment.offering_id}/assignments`,
              token,
            );
            return (courseAssignments.items || []).map((assignment) => ({
              ...assignment,
              course_code: enrollment.course_code,
              course_title: enrollment.course_title,
            }));
          }),
        );
        result = { items: assignments.flat() };
      }
      if (type === "My Profile") {
        setProfile(result.profile || {});
      }
      setData(result);
      navigateToScreen(type, navigationMode);
      if (type !== "Messages") setViewUser(null);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function openGroup(group) {
    setLoading(true);
    setError("");
    try {
      await request(`/groups/${group.id}/join`, token, jsonOptions("POST", {}));
      const result = await request(`/groups/${group.id}/feed`, token);
      setSelectedGroup(group);
      setData(result);
      navigateToScreen("Community");
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function openProfile(userId) {
    setLoading(true);
    setError("");
    try {
      const result = await request(`/users/${userId}/profile`, token);
      setViewUser(result);
      navigateToScreen("Member Profile");
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function openChat(userId) {
    setLoading(true);
    setError("");
    try {
      if (!institution?.id) {
        throw new Error("Join a university before messaging campus members.");
      }
      await request(
        "/communications/conversations",
        token,
        jsonOptions("POST", {
          kind: "direct",
          institution_id: institution.id,
          recipient_id: userId,
        }),
      );
      setViewUser(null);
      navigateToScreen("Messages");
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function perform(path, body, successMessage, reloadScreen = screen) {
    setActionBusy(true);
    setError("");
    try {
      await request(path, token, jsonOptions("POST", body));
      setForm({});
      Alert.alert("Done", successMessage);
      await load(reloadScreen);
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setActionBusy(false);
    }
  }

  async function saveProfile() {
    setActionBusy(true);
    setError("");
    try {
      const result = await request(
        "/profile",
        token,
        jsonOptions("PATCH", profile || {}),
      );
      setProfile(result.profile || profile);
      Alert.alert("Saved", "Your profile has been updated.");
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setActionBusy(false);
    }
  }

  async function changePassword(currentPassword, newPassword) {
    if (newPassword.length < 8) {
      setError("Your new password must be at least 8 characters.");
      return false;
    }
    setActionBusy(true);
    setError("");
    try {
      await request(
        "/auth/change-password",
        token,
        jsonOptions("POST", {
          current_password: currentPassword,
          new_password: newPassword,
        }),
      );
      Alert.alert("Password changed", "Use your new password next time you sign in.");
      return true;
    } catch (changeError) {
      setError(changeError.message);
      return false;
    } finally {
      setActionBusy(false);
    }
  }

  async function saveInstitution() {
    setActionBusy(true);
    setError("");
    try {
      const result = await request(
        `/institutions/${institution.id}/admin/institution`,
        token,
        jsonOptions("PUT", form),
      );
      setInstitution(result.data);
      setData((current) => ({ ...current, institution: result.data }));
      setForm({});
      Alert.alert("Saved", "Institution details have been updated.");
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setActionBusy(false);
    }
  }

  async function mutate(path, method, body, successMessage) {
    setActionBusy(true);
    setError("");
    try {
      await request(path, token, jsonOptions(method, body));
      Alert.alert("Done", successMessage || "Changes saved.");
      await loadAdmin(screen);
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setActionBusy(false);
    }
  }

  async function search() {
    const value = query.trim();
    if (value.length < 2) {
      setError("Enter at least 2 characters to search.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await request(
        `/search/all?q=${encodeURIComponent(value)}`,
        token,
      );
      setData(result);
      navigateToScreen("Search");
    } catch (searchError) {
      setError(searchError.message);
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage(recipientId) {
    const body = form.message?.trim();
    if (!body) {
      setError("Write a message before sending.");
      return;
    }
    setActionBusy(true);
    setError("");
    try {
      await request(
        "/messages",
        token,
        jsonOptions("POST", { recipient_id: recipientId, body }),
      );
      setForm({});
      await openChat(recipientId);
    } catch (sendError) {
      setError(sendError.message);
    } finally {
      setActionBusy(false);
    }
  }

  function choosePrimaryTab(name) {
    setViewUser(null);
    setSelectedAssignment(null);
    load(name, undefined, "reset");
  }

  if (!authReady) {
    return (
      <SafeAreaView style={styles.safe}>
        <StatusBar
          barStyle="dark-content"
          backgroundColor="#ffffff"
          translucent={false}
        />
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#2563eb" />
          <Text style={styles.muted}>Loading CampusHub…</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!token) {
    return (
      <SafeAreaView style={styles.safe}>
        <StatusBar
          barStyle="dark-content"
          backgroundColor="#ffffff"
          translucent={false}
        />
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : undefined}
          style={styles.authScreen}
        >
          <ScrollView
            contentContainerStyle={styles.authScroll}
            keyboardShouldPersistTaps="handled"
          >
            <View style={styles.authCard}>
              <View style={styles.brandMark}>
                <Text style={styles.brandMarkText}>C</Text>
              </View>
              <Text style={styles.logo}>CampusHub</Text>
              <Text style={styles.authSubtitle}>
                {registerMode
                  ? "Create your university account"
                  : "Your university, all in one place"}
              </Text>
              {registerMode && (
                <>
                  <Field
                    label="Full name"
                    value={fullName}
                    onChangeText={setFullName}
                    autoCapitalize="words"
                    returnKeyType="next"
                  />
                  <Field
                    label="Username"
                    value={username}
                    onChangeText={setUsername}
                    autoCapitalize="none"
                    returnKeyType="next"
                  />
                </>
              )}

              <Field
                label="Email"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
                autoComplete="email"
                returnKeyType="next"
              />
              <Field
                label="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoComplete={registerMode ? "new-password" : "current-password"}
                returnKeyType="done"
                onSubmitEditing={authenticate}
              />
              {error ? <ErrorBanner message={error} /> : null}
              <PrimaryButton
                title={registerMode ? "Create account" : "Sign in"}
                onPress={authenticate}
                disabled={authBusy}
                loading={authBusy}
              />
              <TouchableOpacity
                accessibilityRole="button"
                onPress={() => {
                  setRegisterMode((current) => !current);
                  setError("");
                }}
                style={styles.authLinkButton}
              >
                <Text style={styles.link}>
                  {registerMode
                    ? "Already have an account? Sign in"
                    : "Create a new account"}
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  const currentTitle = titleFor(screen);
  const isAdminScreen = Boolean(adminPaths[screen]);
  const items = screenItems(screen, data);
  const unreadCount = (data?.items || []).filter(
    (item) => item.is_read === false,
  ).length;

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar
        barStyle="dark-content"
        backgroundColor="#ffffff"
        translucent={false}
      />
      <View style={styles.appHeader}>
        <View style={styles.headerTitleGroup}>
          <Text style={styles.eyebrow}>
            {isAdminScreen ? "UNIVERSITY ADMIN" : "CAMPUSHUB"}
          </Text>
          <Text numberOfLines={1} style={styles.pageTitle}>
            {screen === "Community" && selectedGroup
              ? selectedGroup.name
              : currentTitle}
          </Text>
          {institution && isAdminScreen ? (
            <Text numberOfLines={1} style={styles.headerSubtitle}>
              {institution.name}
            </Text>
          ) : null}
        </View>
        <View style={styles.headerActions}>
          <IconButton
            accessibilityLabel={
              unreadCount ? `${unreadCount} unread notifications` : "Notifications"
            }
            label={unreadCount ? `♧ ${unreadCount}` : "♧"}
            onPress={() => load("Notifications")}
          />
          <IconButton
            accessibilityLabel="Refresh screen"
            label="↻"
            onPress={() => load(screen)}
          />
        </View>
      </View>

      {error ? <ErrorBanner message={error} /> : null}

      {loading ? (
        <View style={styles.loadingBar}>
          <ActivityIndicator color="#2563eb" />
          <Text style={styles.loadingText}>Loading…</Text>
        </View>
      ) : null}

      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.contentHost}
      >
        <ScrollView
          key={screen}
          style={styles.contentScroll}
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
        >
          {screen === "Home" && (
            <HomeScreen
              data={data}
              institution={institution}
              onOpen={load}
            />
          )}

          {screen === "Courses" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No enrolled courses yet"
              emptyBody="When you register for courses, they will appear here."
            />
          )}

          {screen === "Course Registration" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No courses are open"
              emptyBody="There are no open course offerings for your institution right now."
              renderAction={(item) =>
                item.enrolled ? (
                  <StatusPill label="Enrolled" tone="success" />
                ) : (
                  <SmallButton
                    title="Register"
                    disabled={actionBusy}
                    onPress={() =>
                      perform(
                        `/offerings/${item.id}/enroll`,
                        {},
                        "You are now enrolled in this course.",
                      )
                    }
                  />
                )
              }
            />
          )}

          {screen === "Assignments" && (
            <>
              <ItemList
                screen={screen}
                items={items}
                emptyTitle="No assignments to show"
                emptyBody="Assignments from your enrolled courses will appear here."
                renderAction={(item) => (
                  <SmallButton
                    title={
                      selectedAssignment?.id === item.id
                        ? "Close submission"
                        : "Submit work"
                    }
                    onPress={() =>
                      setSelectedAssignment((current) =>
                        current?.id === item.id ? null : item,
                      )
                    }
                  />
                )}
                renderExtra={(item) =>
                  selectedAssignment?.id === item.id ? (
                    <View style={styles.inlineForm}>
                      <Field
                        label="Your submission"
                        value={form.body || ""}
                        onChangeText={(value) => setField("body", value)}
                        multiline
                        placeholder="Write your answer or submission notes"
                      />
                      <Field
                        label="File link (optional)"
                        value={form.file_url || ""}
                        onChangeText={(value) => setField("file_url", value)}
                        autoCapitalize="none"
                        keyboardType="url"
                      />
                      <PrimaryButton
                        title="Send submission"
                        loading={actionBusy}
                        disabled={actionBusy}
                        onPress={() =>
                          perform(
                            `/assignments/${item.id}/submit`,
                            { body: form.body || "", file_url: form.file_url || "" },
                            "Your assignment has been submitted.",
                          )
                        }
                      />
                    </View>
                  ) : null
                }
              />
            </>
          )}

          {screen === "Attendance" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No attendance records"
              emptyBody="Your attendance will appear after it has been recorded."
            />
          )}

          {screen === "Results" && (
            <>
              <View style={styles.statGrid}>
                <StatCard label="CGPA" value={data?.cgpa ?? "—"} />
                <StatCard label="Credits" value={data?.credits ?? 0} />
              </View>
              <ItemList
                screen={screen}
                items={items}
                emptyTitle="No published results"
                emptyBody="Published grades will appear here."
              />
            </>
          )}

          {screen === "Timetable" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="Your timetable is empty"
              emptyBody="Class times for your enrolled courses will appear here."
            />
          )}

          {screen === "Calendar" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No academic dates yet"
              emptyBody="Institution calendar events will appear here."
            />
          )}

          {screen === "Announcements" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No announcements"
              emptyBody="New institution updates will appear here."
            />
          )}

          {screen === "Groups" && (
            <GroupList items={items} onOpen={openGroup} />
          )}

          {screen === "Community" && (
            <CommunityScreen
              group={selectedGroup}
              items={items}
              form={form}
              setField={setField}
              actionBusy={actionBusy}
              onBack={() => load("Groups")}
              onPost={() =>
                perform(
                  `/groups/${selectedGroup.id}/posts`,
                  { body: form.post || "" },
                  "Your post has been published.",
                )
              }
              onReact={(postId) =>
                perform(
                  `/posts/${postId}/reactions`,
                  { reaction: "like" },
                  "Reaction added.",
                  "Community",
                )
              }
            />
          )}

          {screen === "Events" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No upcoming events"
              emptyBody="Events from your institution will appear here."
              renderAction={(item) => (
                <SmallButton
                  title="Register"
                  disabled={actionBusy}
                  onPress={() =>
                    perform(
                      `/events/${item.id}/register`,
                      {},
                      "You are registered for this event.",
                    )
                  }
                />
              )}
            />
          )}

          {screen === "Clubs" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No clubs listed"
              emptyBody="Clubs at your institution will appear here."
              renderAction={(item) => (
                <SmallButton
                  title="Join club"
                  disabled={actionBusy}
                  onPress={() =>
                    perform(
                      `/clubs/${item.id}/join`,
                      {},
                      "You have joined the club.",
                    )
                  }
                />
              )}
            />
          )}

          {screen === "Documents" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No shared documents"
              emptyBody="Documents shared by your institution will appear here."
              renderAction={(item) =>
                item.url ? (
                  <SmallButton
                    title="Open document"
                    onPress={() =>
                      Linking.openURL(item.url).catch((openError) =>
                        setError(openError.message),
                      )
                    }
                  />
                ) : null
              }
            />
          )}

          {screen === "Services" && (
            <>
              <RequestForm
                title="New service request"
                fields={[
                  ["Request type", "request_type"],
                  ["Details", "details"],
                ]}
                form={form}
                setField={setField}
                actionBusy={actionBusy}
                submitTitle="Send request"
                onSubmit={() =>
                  perform(
                    "/service-requests",
                    {
                      request_type: form.request_type || "general",
                      details: form.details || "",
                      institution_id: institution?.id,
                    },
                    "Your service request has been sent.",
                  )
                }
              />
              <ItemList
                screen={screen}
                items={items}
                emptyTitle="No previous requests"
                emptyBody="Your service requests and their status will appear here."
              />
            </>
          )}

          {screen === "Certificates" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No certificates yet"
              emptyBody="Certificates issued to you will appear here."
            />
          )}

          {screen === "Campus" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No campus services listed"
              emptyBody="Campus services and their contact details will appear here."
            />
          )}

          {screen === "Library" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No library items found"
              emptyBody="The institution library collection will appear here."
              renderAction={(item) =>
                item.available_copies > 0 ? (
                  <SmallButton
                    title="Borrow"
                    disabled={actionBusy}
                    onPress={() =>
                      perform(
                        `/library/items/${item.id}/borrow`,
                        {},
                        "The item has been checked out to you.",
                      )
                    }
                  />
                ) : (
                  <StatusPill label="Unavailable" />
                )
              }
            />
          )}

          {screen === "My library loans" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No active loans"
              emptyBody="Books you borrow will appear here."
              renderAction={(item) =>
                item.returned_at ? (
                  <StatusPill label="Returned" tone="success" />
                ) : (
                  <SmallButton
                    title="Return"
                    disabled={actionBusy}
                    onPress={() =>
                      perform(
                        `/library/loans/${item.id}/return`,
                        {},
                        "The book has been returned.",
                      )
                    }
                  />
                )
              }
            />
          )}

          {screen === "Hostel" && (
            <>
              <RequestForm
                title="Apply for a hostel room"
                fields={[["Application details", "details"]]}
                form={form}
                setField={setField}
                actionBusy={actionBusy}
                submitTitle="Submit application"
                onSubmit={() =>
                  perform(
                    `/hostel/${institution?.id}/apply`,
                    { details: form.details || "" },
                    "Your hostel application has been submitted.",
                  )
                }
              />
              <ItemList
                screen={screen}
                items={items}
                emptyTitle="No rooms listed"
                emptyBody="Available hostel rooms will appear here."
              />
            </>
          )}

          {screen === "Lost & Found" && (
            <>
              <RequestForm
                title="Report a lost or found item"
                fields={[
                  ["Type (lost or found)", "item_type"],
                  ["Item name", "title"],
                  ["Description", "description"],
                  ["Location", "location"],
                  ["Contact information", "contact"],
                ]}
                form={form}
                setField={setField}
                actionBusy={actionBusy}
                submitTitle="Post report"
                onSubmit={() =>
                  perform(
                    `/institutions/${institution?.id}/lost-found`,
                    {
                      item_type: form.item_type || "lost",
                      title: form.title || "",
                      description: form.description || "",
                      location: form.location || "",
                      contact: form.contact || "",
                    },
                    "Your report has been posted.",
                  )
                }
              />
              <ItemList
                screen={screen}
                items={items}
                emptyTitle="Nothing reported yet"
                emptyBody="Lost and found reports for your institution will appear here."
              />
            </>
          )}

          {screen === "Fees" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="No fee records"
              emptyBody="Your university fee records will appear here."
            />
          )}

          {["Bus Routes", "Emergency Contacts", "Cafeteria Menu"].includes(screen) && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle={`No ${screen.toLowerCase()} available`}
              emptyBody="Your university has not published any information here yet."
            />
          )}

          {screen === "Student Requests" && (
            <>
              <RequestForm
                title="Create a student request"
                fields={[
                  ["Request type", "request_type"],
                  ["Details", "details"],
                ]}
                form={form}
                setField={setField}
                actionBusy={actionBusy}
                submitTitle="Submit request"
                onSubmit={() =>
                  perform(
                    "/service-requests/advanced",
                    {
                      ...form,
                      institution_id: institution?.id,
                    },
                    "Your request was submitted.",
                  )
                }
              />
              <ItemList
                screen={screen}
                items={items}
                emptyTitle="No student requests"
                emptyBody="Requests and their progress will appear here."
              />
            </>
          )}

          {screen === "Messages" && !viewUser && (
            <CommunicationCenter token={token} institution={institution} />
          )}

          {screen === "Messages" && viewUser && (
            <MessagesScreen
              items={viewUser ? viewMessages : items}
              user={viewUser}
              currentUserId={userId}
              form={form}
              setField={setField}
              actionBusy={actionBusy}
              onOpenChat={openChat}
              onBack={() => {
                setViewUser(null);
                load("Messages");
              }}
              onSend={() => sendMessage(viewUser?.user_id)}
            />
          )}

          {screen === "Notifications" && (
            <ItemList
              screen={screen}
              items={items}
              emptyTitle="You are all caught up"
              emptyBody="New notifications will show up here."
              renderAction={(item) =>
                item.is_read ? (
                  <StatusPill label="Read" tone="success" />
                ) : (
                  <SmallButton
                    title="Mark as read"
                    disabled={actionBusy}
                    onPress={() =>
                      perform(
                        `/notifications/${item.id}/read`,
                        {},
                        "Notification marked as read.",
                      )
                    }
                  />
                )
              }
            />
          )}

          {screen === "Search" && (
            <>
              <View style={styles.panel}>
                <Text style={styles.panelTitle}>Search CampusHub</Text>
                <Field
                  label="People, courses, or departments"
                  value={query}
                  onChangeText={setQuery}
                  autoCapitalize="none"
                  returnKeyType="search"
                  onSubmitEditing={search}
                />
                <PrimaryButton title="Search" onPress={search} />
              </View>
              <ItemList
                screen={screen}
                items={items}
                renderAction={(item) =>
                  item.type === "student_or_user" ? (
                    <View style={styles.buttonRow}>
                      <SmallButton
                        title="Profile"
                        onPress={() => openProfile(item.id)}
                      />
                      <SmallButton
                        title="Message"
                        onPress={() => openChat(item.id)}
                      />
                    </View>
                  ) : null
                }
                emptyTitle="Search for something"
                emptyBody="Enter at least 2 characters to find people, courses, or departments."
              />
            </>
          )}

          {screen === "My Profile" && (
            <ProfileScreen
              profile={profile || {}}
              setProfile={setProfile}
              actionBusy={actionBusy}
              onSave={saveProfile}
              onChangePassword={changePassword}
              onLogout={logout}
            />
          )}

          {screen === "My University" && (
            <UniversityScreen
              token={token}
              currentInstitution={institution}
              onSelect={setInstitution}
              onProfile={() => load("My Profile")}
            />
          )}

          {screen === "Member Profile" && (
            <MemberProfileScreen
              user={viewUser}
              onMessage={() => openChat(viewUser?.user_id)}
            />
          )}

          {screen === "Platform Admin" && platformAdmin && (
            <PlatformAdminScreen
              token={token}
              selectedInstitution={institution}
              onSelectInstitution={setInstitution}
            />
          )}

          {screen === "Teaching" && institution?.role === "teacher" && (
            <TeachingScreen token={token} />
          )}

          {screen === "More" && (
            <MoreScreen
              groups={
                [
                  ...featureGroups,
                  ...(institution?.role === "teacher"
                    ? [{
                        title: "Teaching",
                        description: "Support your students and manage assigned courses.",
                        items: [
                          ["Teaching", "Course rosters, assignments, grading, and attendance"],
                        ],
                      }]
                    : []),
                  ...(platformAdmin
                    ? [{
                        title: "Platform operations",
                        description: "Central oversight for all CampusHub universities.",
                        items: [
                          ["Platform Admin", "Manage tenants, memberships, and institutional ownership"],
                        ],
                      }]
                    : []),
                ]
              }
              onOpen={load}
              onAdmin={() => load("Admin")}
              onLogout={logout}
            />
          )}

          {screen === "Admin" && (
            <AdminHome
              institutions={admins}
              selectedId={institution?.id}
              onChoose={(nextInstitution) => {
                setInstitution(nextInstitution);
                loadAdmin("overview", nextInstitution.id);
              }}
            />
          )}

          {isAdminScreen && screen === "overview" && (
            <AdminOverview
              data={data}
              onChoose={(section) => loadAdmin(section)}
            />
          )}

          {isAdminScreen && screen === "institution" && (
            <View style={styles.panel}>
              <Text style={styles.panelTitle}>Institution details</Text>
              {[
                ["Name", "name"],
                ["Slug", "slug"],
                ["Type", "kind"],
                ["Address", "address"],
                ["Website", "website"],
                ["Description", "description"],
              ].map(([label, key]) => (
                <Field
                  key={key}
                  label={label}
                  value={form[key] ?? data?.institution?.[key] ?? ""}
                  onChangeText={(value) => setField(key, value)}
                  multiline={key === "description"}
                  autoCapitalize={key === "website" || key === "slug" ? "none" : "sentences"}
                />
              ))}
              <PrimaryButton
                title="Save institution"
                loading={actionBusy}
                disabled={actionBusy}
                onPress={saveInstitution}
              />
            </View>
          )}

          {isAdminScreen && screen !== "overview" && screen !== "institution" && (
            <View>
              <SecondaryButton
                title="← All admin tools"
                onPress={() => loadAdmin("overview")}
              />
              <ItemList
                screen={screen}
                items={items}
                emptyTitle={`No ${currentTitle.toLowerCase()} found`}
                emptyBody="Items for this institution will appear here."
                renderAdminItem={(item) => (
                  <AdminRow
                    item={item}
                    screen={screen}
                    institutionId={institution?.id}
                    onMutate={mutate}
                  />
                )}
              />
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>

      <View style={styles.bottomNav}>
        {primaryTabs.map(([name, icon]) => {
          const active =
            name === "More"
              ? screen === "More" ||
                screen === "Teaching" ||
                screen === "My Profile" ||
                screen === "My University" ||
                screen === "Platform Admin" ||
                screen === "Admin" ||
                screen === "overview" ||
                isAdminScreen
              : name === "Home"
                ? screen === "Home"
                : name === "Courses"
                  ? ["Courses", "Course Registration", "Assignments", "Attendance", "Results", "Timetable"].includes(screen)
                  : ["Campus", ...featureGroups[1].items.map(([item]) => item)].includes(screen);
          return (
            <TouchableOpacity
              key={name}
              accessibilityRole="button"
              accessibilityState={{ selected: active }}
              onPress={() => choosePrimaryTab(name)}
              style={[styles.navButton, active && styles.navButtonActive]}
            >
              <Text style={[styles.navIcon, active && styles.navTextActive]}>
                {icon}
              </Text>
              <Text style={[styles.navLabel, active && styles.navTextActive]}>
                {name}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

function HomeScreen({ data, institution, onOpen }) {
  const stats = data?.stats || {};
  const shortcuts = [
    ["My University", institution?.name ? "Manage your university membership" : "Find or create your university"],
    ["Course Registration", "Find an open course"],
    ["Timetable", "Check today's classes"],
    ["Announcements", "Read university updates"],
    ["Events", "See what's happening"],
  ];
  return (
    <View>
      <View style={styles.welcomePanel}>
        <Text style={styles.eyebrow}>YOUR CAMPUS, CONNECTED</Text>
        <Text style={styles.welcomeTitle}>
          {institution?.name ? `Welcome to ${institution.name}` : "Welcome back"}
        </Text>
        <Text style={styles.welcomeBody}>
          See your courses, keep up with campus life, and manage your university
          account.
        </Text>
      </View>
      <View style={styles.statGrid}>
        <StatCard label="Courses" value={stats.courses ?? 0} />
        <StatCard label="Assignments" value={stats.upcoming_assignments ?? 0} />
        <StatCard
          label="Attendance"
          value={`${stats.attendance_percent ?? 0}%`}
        />
        <StatCard label="Unread" value={stats.unread_notifications ?? 0} />
      </View>
      <SectionHeading title="Quick access" />
      <View style={styles.shortcutGrid}>
        {shortcuts.map(([name, description]) => (
          <TouchableOpacity
            key={name}
            accessibilityRole="button"
            onPress={() => onOpen(name)}
            style={styles.shortcutCard}
          >
            <Text style={styles.shortcutTitle}>{name}</Text>
            <Text style={styles.shortcutBody}>{description}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <SectionHeading title="Upcoming assignments" />
      {(data?.assignments || []).length ? (
        data.assignments.map((assignment) => (
          <View key={assignment.id} style={styles.itemCard}>
            <Text style={styles.itemTitle}>{assignment.title}</Text>
            {assignment.due_at ? (
              <Text style={styles.itemDetail}>
                Due {formatDate(assignment.due_at)}
              </Text>
            ) : null}
            {assignment.description ? (
              <Text style={styles.itemBody}>{assignment.description}</Text>
            ) : null}
          </View>
        ))
      ) : (
        <EmptyState
          title="Nothing due right now"
          body="Your upcoming assignments will show up here."
          compact
        />
      )}
      <SectionHeading title="University administration" />
      <View style={styles.panel}>
        <Text style={styles.panelBody}>
          Manage institution members, academic sections, events, and requests.
        </Text>
        <PrimaryButton
          title="Open admin tools"
          onPress={() => onOpen("Admin")}
        />
      </View>
    </View>
  );
}

function MoreScreen({ groups, onOpen, onAdmin, onLogout }) {
  return (
    <View>
      <Text style={styles.introText}>
        Browse all the tools available in your CampusHub account.
      </Text>
      {groups.map((group) => (
        <View key={group.title} style={styles.featureSection}>
          <SectionHeading title={group.title} />
          <Text style={styles.sectionDescription}>{group.description}</Text>
          <View style={styles.shortcutGrid}>
            {group.items.map(([name, description]) => (
              <TouchableOpacity
                key={name}
                accessibilityRole="button"
                onPress={() => onOpen(name)}
                style={styles.shortcutCard}
              >
                <Text style={styles.shortcutTitle}>{name}</Text>
                <Text style={styles.shortcutBody}>{description}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ))}
      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Institution administration</Text>
        <Text style={styles.panelBody}>
          Open the tools available for institutions you manage.
        </Text>
        <PrimaryButton title="Open admin tools" onPress={onAdmin} />
      </View>
      <SecondaryButton title="Sign out" onPress={onLogout} />
    </View>
  );
}

function TeachingScreen({ token }) {
  const [dashboard, setDashboard] = useState(null);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [courseData, setCourseData] = useState(null);
  const [assignmentTitle, setAssignmentTitle] = useState("");
  const [assignmentDescription, setAssignmentDescription] = useState("");
  const [assignmentDue, setAssignmentDue] = useState("");
  const [assignmentMaxScore, setAssignmentMaxScore] = useState("100");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function refreshDashboard() {
    setError("");
    setLoading(true);
    try {
      const result = await request("/teacher/dashboard", token);
      setDashboard(result);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshDashboard();
  }, [token]);

  async function openCourse(course) {
    setLoading(true);
    setError("");
    try {
      const [students, attendance, assignments] = await Promise.all([
        request(`/teacher/courses/${course.id}/students`, token),
        request(`/teacher/attendance/${course.id}`, token),
        request(`/offerings/${course.id}/assignments`, token),
      ]);
      const assignmentItems = await Promise.all(
        (assignments.items || []).map(async (assignment) => ({
          ...assignment,
          submissions: (
            await request(
              `/teacher/assignments/${assignment.id}/submissions`,
              token,
            )
          ).items || [],
        })),
      );
      setSelectedCourse(course);
      setCourseData({
        students: students.items || [],
        attendance: attendance.items || [],
        assignments: assignmentItems,
      });
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function createAssignment() {
    const title = assignmentTitle.trim();
    const maxScore = Number(assignmentMaxScore);
    if (!selectedCourse || !title || !Number.isFinite(maxScore) || maxScore <= 0) {
      setError("Enter an assignment title and a positive maximum score.");
      return;
    }
    let dueAt = null;
    if (assignmentDue.trim()) {
      const parsed = new Date(assignmentDue);
      if (Number.isNaN(parsed.getTime())) {
        setError("Enter a valid assignment deadline.");
        return;
      }
      dueAt = parsed.toISOString();
    }
    setBusy(true);
    setError("");
    try {
      await request(
        `/offerings/${selectedCourse.id}/assignments`,
        token,
        jsonOptions("POST", {
          title,
          description: assignmentDescription.trim(),
          max_score: maxScore,
          due_at: dueAt,
        }),
      );
      setAssignmentTitle("");
      setAssignmentDescription("");
      setAssignmentDue("");
      await openCourse(selectedCourse);
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setBusy(false);
    }
  }

  async function markAttendance() {
    if (!selectedCourse || !courseData?.students.length) {
      setError("There are no enrolled students to record.");
      return;
    }
    Alert.alert(
      "Record today's attendance?",
      "This will mark every currently enrolled student as present for today.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Mark all present",
          onPress: async () => {
            setBusy(true);
            setError("");
            try {
              await request(
                `/offerings/${selectedCourse.id}/attendance`,
                token,
                jsonOptions("POST", {
                  records: courseData.students.map((item) => ({
                    student_id: item.student_id,
                    status: "present",
                  })),
                }),
              );
              await openCourse(selectedCourse);
            } catch (actionError) {
              setError(actionError.message);
            } finally {
              setBusy(false);
            }
          },
        },
      ],
    );
  }

  async function gradeSubmission(submission, maxScore) {
    const score = Number(submission.scoreInput);
    if (!Number.isFinite(score) || score < 0 || score > maxScore) {
      setError(`Enter a score between 0 and ${maxScore}.`);
      return;
    }
    setBusy(true);
    setError("");
    try {
      await request(
        `/submissions/${submission.id}/grade`,
        token,
        jsonOptions("POST", {
          score,
          feedback: submission.feedbackInput || "",
        }),
      );
      await openCourse(selectedCourse);
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading && !dashboard) {
    return <ActivityIndicator color="#2563eb" style={styles.loadingContent} />;
  }
  return (
    <View>
      {error ? <ErrorBanner message={error} /> : null}
      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Teaching dashboard</Text>
        <Text style={styles.panelBody}>
          Review class rosters, assignments, submissions, grades, and attendance.
        </Text>
        <View style={styles.statGrid}>
          <StatCard label="Courses" value={dashboard?.stats?.courses ?? 0} />
          <StatCard label="Students" value={dashboard?.stats?.students ?? 0} />
          <StatCard label="Assignments" value={dashboard?.stats?.assignments ?? 0} />
          <StatCard label="Submissions" value={dashboard?.stats?.submissions ?? 0} />
        </View>
        <SecondaryButton title="Refresh courses" onPress={refreshDashboard} />
      </View>
      {selectedCourse && courseData ? (
        <View style={styles.panel}>
          <SecondaryButton
            title="← All teaching courses"
            onPress={() => {
              setSelectedCourse(null);
              setCourseData(null);
              setError("");
            }}
          />
          <Text style={styles.panelTitle}>
            {selectedCourse.course_code
              ? `${selectedCourse.course_code} · ${selectedCourse.course_title}`
              : `Course offering #${selectedCourse.id}`}
          </Text>
          <Text style={styles.panelBody}>
            {courseData.students.length} enrolled students ·{" "}
            {courseData.assignments.length} assignments
          </Text>
          <PrimaryButton
            title="Mark all enrolled students present today"
            disabled={busy}
            onPress={markAttendance}
          />
          <SectionHeading title="Student roster" />
          {courseData.students.map((student) => {
            const records = courseData.attendance.filter(
              (record) => record.student_id === student.student_id,
            );
            return (
              <View key={student.student_id} style={styles.itemCard}>
                <Text style={styles.itemTitle}>
                  Student #{student.student_id}
                </Text>
                <Text style={styles.itemDetail}>
                  Attendance records: {records.length} · Enrolment: {student.status}
                </Text>
              </View>
            );
          })}
          <SectionHeading title="Create an assignment" />
          <Field
            label="Assignment title"
            value={assignmentTitle}
            onChangeText={setAssignmentTitle}
          />
          <Field
            label="Instructions"
            value={assignmentDescription}
            onChangeText={setAssignmentDescription}
            multiline
          />
          <Field
            label="Deadline (date and time)"
            value={assignmentDue}
            onChangeText={setAssignmentDue}
            placeholder="e.g. 2026-12-15T17:00"
          />
          <Field
            label="Maximum score"
            value={assignmentMaxScore}
            onChangeText={setAssignmentMaxScore}
            keyboardType="decimal-pad"
          />
          <PrimaryButton
            title="Publish assignment"
            loading={busy}
            disabled={busy}
            onPress={createAssignment}
          />
          <SectionHeading title="Assignments and submissions" />
          {courseData.assignments.map((assignment) => (
            <View key={assignment.id} style={styles.itemCard}>
              <Text style={styles.itemTitle}>{assignment.title}</Text>
              <Text style={styles.itemDetail}>
                {assignment.submissions.length} submissions · Max score{" "}
                {assignment.max_score}
              </Text>
              {assignment.submissions.map((submission) => (
                <TeacherSubmissionRow
                  key={submission.id}
                  submission={submission}
                  maxScore={assignment.max_score}
                  disabled={busy}
                  onSave={(values) =>
                    gradeSubmission(values, assignment.max_score)
                  }
                />
              ))}
            </View>
          ))}
        </View>
      ) : (
        <View>
          {(dashboard?.courses || []).map((course) => (
            <TouchableOpacity
              key={course.id}
              accessibilityRole="button"
              onPress={() => openCourse(course)}
              style={styles.itemCard}
            >
              <Text style={styles.itemTitle}>
                {course.course_code
                  ? `${course.course_code} · ${course.course_title}`
                  : `Course offering #${course.id}`}
              </Text>
              <Text style={styles.itemDetail}>
                Section {course.section || "—"} · Room {course.room || "—"}
              </Text>
              <Text style={styles.actionLink}>Open teaching tools →</Text>
            </TouchableOpacity>
          ))}
          {!dashboard?.courses?.length && !loading ? (
            <EmptyState
              title="No assigned courses"
              body="Your institution administrator can assign you as the teacher of a course offering."
            />
          ) : null}
        </View>
      )}
    </View>
  );
}

function TeacherSubmissionRow({ submission, maxScore, disabled, onSave }) {
  const [score, setScore] = useState(
    submission.score == null ? "" : String(submission.score),
  );
  const [feedback, setFeedback] = useState(submission.feedback || "");
  return (
    <View style={styles.nestedCard}>
      <Text style={styles.itemDetail}>
        Submission #{submission.id} · Student #{submission.student_id}
      </Text>
      <Text style={styles.itemBody}>
        {submission.body || submission.file_url || "No text content attached"}
      </Text>
      {submission.file_url ? (
        <Text style={styles.itemDetail}>{submission.file_url}</Text>
      ) : null}
      <Field
        label={`Score (out of ${maxScore})`}
        value={score}
        onChangeText={setScore}
        keyboardType="decimal-pad"
      />
      <Field
        label="Feedback"
        value={feedback}
        onChangeText={setFeedback}
        multiline
      />
      <SmallButton
        title="Save grade and feedback"
        disabled={disabled}
        onPress={() => onSave({ ...submission, scoreInput: score, feedbackInput: feedback })}
      />
    </View>
  );
}

function UniversityScreen({ token, currentInstitution, onSelect, onProfile }) {
  const [memberships, setMemberships] = useState([]);
  const [institutions, setInstitutions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [departmentId, setDepartmentId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [program, setProgram] = useState("");
  const [session, setSession] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    setFetching(true);
    Promise.all([
      request("/my/institutions", token),
      request("/institutions", token),
    ])
      .then(([membershipResult, institutionResult]) => {
        if (!active) return;
        setError("");
        setMemberships(membershipResult.items || []);
        setInstitutions(institutionResult.items || []);
      })
      .catch((loadError) => {
        if (active) setError(loadError.message);
      })
      .finally(() => {
        if (active) setFetching(false);
      });
    return () => {
      active = false;
    };
  }, [token, reloadKey]);

  async function chooseInstitution(item) {
    setSelected(item);
    setDepartments([]);
    setDepartmentId("");
    setNotice("");
    setError("");
    try {
      const result = await request(`/institutions/${item.id}/departments`, token);
      setDepartments(result.items || []);
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  async function applyToInstitution() {
    if (
      !selected ||
      !departmentId ||
      !studentId.trim() ||
      !program.trim() ||
      !session.trim() ||
      !academicYear.trim()
    ) {
      setError("Choose a department and enter your student ID, program, session, and academic year.");
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await request(
        `/institutions/${selected.id}/join`,
        token,
        jsonOptions("POST", {
          department_id: Number(departmentId),
          student_id: studentId.trim(),
          program: program.trim(),
          session: session.trim(),
          academic_year: academicYear.trim(),
        }),
      );
      setNotice(`Your request to join ${selected.name} was submitted for approval.`);
      setStudentId("");
      setProgram("");
      setSession("");
      setAcademicYear("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function createInstitution() {
    if (!name.trim() || !slug.trim()) {
      setError("Enter an institution name and URL slug.");
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const created = await request(
        "/institutions",
        token,
        jsonOptions("POST", {
          name: name.trim(),
          slug: slug.trim().toLowerCase(),
          kind: "university",
        }),
      );
      const result = await request("/my/institutions", token);
      const createdMembership = (result.items || []).find(
        (item) => item.id === created.id,
      );
      setMemberships(result.items || []);
      setName("");
      setSlug("");
      setNotice("Your university was created.");
      setReloadKey((key) => key + 1);
      if (createdMembership) onSelect(createdMembership);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  const memberIds = new Set(memberships.map((item) => item.id));
  const availableInstitutions = institutions.filter(
    (item) => !memberIds.has(item.id),
  );
  const errorMessage =
    error === "complete_profile_first"
      ? "Complete your profile before creating or joining a university."
      : error;
  return (
    <View>
      <Text style={styles.introText}>
        Your account can belong to more than one university. Select an active
        membership, apply to join a campus, or create a new university.
      </Text>
      <SecondaryButton
        title="Refresh university list"
        onPress={() => setReloadKey((key) => key + 1)}
      />
      {errorMessage ? <ErrorBanner message={errorMessage} /> : null}
      {notice ? <Text style={styles.successNotice}>{notice}</Text> : null}
      <View style={styles.panel}>
        <Text style={styles.panelTitle}>My universities</Text>
        {memberships.length ? (
          memberships.map((item) => (
            <View key={item.id} style={styles.itemCard}>
              <Text style={styles.itemTitle}>{item.name}</Text>
              <Text style={styles.itemDetail}>
                {item.role || "Member"}
                {item.program ? ` · ${item.program}` : ""}
              </Text>
              {currentInstitution?.id === item.id ? (
                <StatusPill label="Currently selected" tone="success" />
              ) : fetching ? (
                <ActivityIndicator color="#2563eb" />
              ) : (
                <SmallButton
                  title="Select university"
                  onPress={() => onSelect(item)}
                />
              )}
            </View>
          ))
        ) : (
          <EmptyState
            title="No university memberships yet"
            body="Apply to a university below, or create one if you administer a campus."
          />
        )}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Find a university</Text>
        {availableInstitutions.length ? (
          availableInstitutions.map((item) => (
              <TouchableOpacity
                key={item.id}
                accessibilityRole="button"
                onPress={() => chooseInstitution(item)}
                style={[
                  styles.itemCard,
                  selected?.id === item.id && styles.itemCardSelected,
                ]}
              >
                <Text style={styles.itemTitle}>{item.name}</Text>
                <Text style={styles.itemDetail}>
                  {item.kind || "University"}
                  {item.address ? ` · ${item.address}` : ""}
                </Text>
                <Text style={styles.actionLink}>Apply to join →</Text>
              </TouchableOpacity>
            ))
        ) : fetching ? (
          <ActivityIndicator color="#2563eb" />
        ) : (
          <Text style={styles.panelBody}>
            No other universities are listed right now.
          </Text>
        )}
      </View>

      {selected ? (
        <View style={styles.panel}>
          <Text style={styles.panelTitle}>Apply to {selected.name}</Text>
          <Text style={styles.panelBody}>
            Your application will be reviewed by the university before
            membership is activated.
          </Text>
          <Text style={styles.fieldLabel}>Department</Text>
          {departments.length ? (
            departments.map((department) => (
              <TouchableOpacity
                key={department.id}
                accessibilityRole="button"
                accessibilityState={{
                  selected: String(department.id) === departmentId,
                }}
                onPress={() => setDepartmentId(String(department.id))}
                style={[
                  styles.itemCard,
                  String(department.id) === departmentId &&
                    styles.itemCardSelected,
                ]}
              >
                <Text style={styles.itemTitle}>{department.name}</Text>
                <Text style={styles.itemDetail}>{department.code}</Text>
              </TouchableOpacity>
            ))
          ) : (
            <Text style={styles.panelBody}>
              This university has no departments available for applications.
            </Text>
          )}
          <Field
            label="Student ID"
            value={studentId}
            onChangeText={setStudentId}
            autoCapitalize="characters"
          />
          <Field label="Program" value={program} onChangeText={setProgram} />
          <Field
            label="Session"
            value={session}
            onChangeText={setSession}
            placeholder="e.g. 2025–2026"
          />
          <Field
            label="Academic year"
            value={academicYear}
            onChangeText={setAcademicYear}
            placeholder="e.g. Year 1"
          />
          {error === "complete_profile_first" ? (
            <SecondaryButton
              title="Complete your profile"
              onPress={onProfile}
            />
          ) : null}
          <PrimaryButton
            title="Submit join request"
            loading={busy}
            disabled={busy || !departments.length}
            onPress={applyToInstitution}
          />
        </View>
      ) : null}

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Create a university</Text>
        <Text style={styles.panelBody}>
          Create an institution if you are responsible for setting up its
          CampusHub space.
        </Text>
        <Field label="University name" value={name} onChangeText={setName} />
        <Field
          label="Unique URL slug"
          value={slug}
          onChangeText={setSlug}
          autoCapitalize="none"
        />
        {error === "complete_profile_first" ? (
          <SecondaryButton
            title="Complete your profile"
            onPress={onProfile}
          />
        ) : null}
        <PrimaryButton
          title="Create university"
          loading={busy}
          disabled={busy}
          onPress={createInstitution}
        />
      </View>
    </View>
  );
}

function PlatformAdminScreen({ token, selectedInstitution, onSelectInstitution }) {
  const [overview, setOverview] = useState(null);
  const [institutions, setInstitutions] = useState([]);
  const [institutionId, setInstitutionId] = useState(
    selectedInstitution?.id ? String(selectedInstitution.id) : "",
  );
  const [members, setMembers] = useState([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("student");
  const [userQuery, setUserQuery] = useState("");
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const roles = [
    "student",
    "teacher",
    "class_representative",
    "media_manager",
    "department_admin",
    "dean",
    "principal",
    "institution_admin",
    "institution_owner",
  ];

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      request("/platform/admin/overview", token),
      request("/platform/admin/institutions", token),
    ])
      .then(([overviewResult, institutionResult]) => {
        if (!active) return;
        const items = institutionResult.items || [];
        setOverview(overviewResult.counts || {});
        setInstitutions(items);
        const selected = items.find(
          (item) => String(item.id) === String(selectedInstitution?.id),
        ) || items[0];
        setInstitutionId(selected ? String(selected.id) : "");
        if (selected) onSelectInstitution(selected);
        setError("");
      })
      .catch((loadError) => {
        if (active) setError(loadError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token, onSelectInstitution, selectedInstitution?.id]);

  useEffect(() => {
    if (!institutionId) {
      setMembers([]);
      return undefined;
    }
    let active = true;
    request(`/platform/admin/members?institution_id=${institutionId}`, token)
      .then((result) => {
        if (active) setMembers(result.items || []);
      })
      .catch((loadError) => {
        if (active) setError(loadError.message);
      });
    return () => {
      active = false;
    };
  }, [token, institutionId]);

  async function reload() {
    setError("");
    setLoading(true);
    try {
      const [overviewResult, institutionResult] = await Promise.all([
        request("/platform/admin/overview", token),
        request("/platform/admin/institutions", token),
      ]);
      setOverview(overviewResult.counts || {});
      setInstitutions(institutionResult.items || []);
      if (institutionId) {
        const memberResult = await request(
          `/platform/admin/members?institution_id=${institutionId}`,
          token,
        );
        setMembers(memberResult.items || []);
      }
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function addMember() {
    if (!institutionId || !email.trim()) {
      setError("Choose a university and enter the registered user's email.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await request(
        `/platform/admin/institutions/${institutionId}/members`,
        token,
        jsonOptions("POST", { email: email.trim(), role }),
      );
      setEmail("");
      await reload();
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setBusy(false);
    }
  }

  async function updateMember(memberId, changes) {
    setBusy(true);
    setError("");
    try {
      await request(
        `/platform/admin/members/${memberId}`,
        token,
        jsonOptions("PATCH", changes),
      );
      await reload();
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setBusy(false);
    }
  }

  async function searchUsers() {
    setError("");
    try {
      const result = await request(
        `/platform/admin/users?q=${encodeURIComponent(userQuery.trim())}`,
        token,
      );
      setUsers(result.items || []);
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  const metrics = [
    ["Universities", "universities"],
    ["Users", "users"],
    ["Active memberships", "active_memberships"],
    ["Pending applications", "pending_requests"],
    ["Courses", "courses"],
    ["Enrolled students", "enrollments"],
  ];
  return (
    <View>
      {error ? <ErrorBanner message={error} /> : null}
      <Text style={styles.introText}>
        System-wide operations are restricted to configured CampusHub platform
        administrators. Tenant roles and owner transfers are audited through the central membership controls.
      </Text>
      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Platform overview</Text>
        {loading && !overview ? (
          <ActivityIndicator color="#2563eb" />
        ) : (
          <View style={styles.statGrid}>
            {metrics.map(([label, key]) => (
              <StatCard key={key} label={label} value={overview?.[key] ?? 0} />
            ))}
          </View>
        )}
        <SecondaryButton title="Refresh platform data" onPress={reload} />
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>University tenants</Text>
        {institutions.length ? institutions.map((item) => (
          <TouchableOpacity
            key={item.id}
            accessibilityRole="button"
            accessibilityState={{ selected: String(item.id) === institutionId }}
            onPress={() => {
              setInstitutionId(String(item.id));
              onSelectInstitution(item);
            }}
            style={[
              styles.itemCard,
              String(item.id) === institutionId && styles.itemCardSelected,
            ]}
          >
            <Text style={styles.itemTitle}>{item.name}</Text>
            <Text style={styles.itemDetail}>
              Owner: {item.owner_email || "Unassigned"} · {item.active_members} active
              {item.pending_requests ? ` · ${item.pending_requests} pending requests` : ""}
            </Text>
          </TouchableOpacity>
        )) : (
          <EmptyState
            title="No universities"
            body="Universities created by students and staff will appear here."
          />
        )}
      </View>

      {institutionId ? (
        <View style={styles.panel}>
          <Text style={styles.panelTitle}>Manage tenant memberships</Text>
          <Text style={styles.panelBody}>
            Roles: {roles.join(", ")}. Assigning institution_owner safely transfers ownership.
          </Text>
          <Field
            label="Registered user email"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />
          <Field
            label="Membership role"
            value={role}
            onChangeText={setRole}
            autoCapitalize="none"
          />
          <PrimaryButton
            title="Add or reactivate member"
            loading={busy}
            disabled={busy}
            onPress={addMember}
          />
          {members.map((member) => (
            <PlatformMemberRow
              key={member.id}
              member={member}
              roles={roles}
              disabled={busy}
              onSave={(nextRole) => updateMember(member.id, { role: nextRole })}
              onToggleStatus={() =>
                updateMember(member.id, {
                  status: member.status === "active" ? "suspended" : "active",
                })
              }
            />
          ))}
        </View>
      ) : null}

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Find a platform user</Text>
        <Field
          label="Name, username, or email"
          value={userQuery}
          onChangeText={setUserQuery}
          autoCapitalize="none"
          returnKeyType="search"
          onSubmitEditing={searchUsers}
        />
        <PrimaryButton title="Search users" onPress={searchUsers} />
        {users.map((user) => (
          <View key={user.id} style={styles.itemCard}>
            <Text style={styles.itemTitle}>{user.full_name}</Text>
            <Text style={styles.itemDetail}>
              {user.email} · {user.memberships} memberships · {user.active_memberships} active
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function PlatformMemberRow({ member, roles, disabled, onSave, onToggleStatus }) {
  const [role, setRole] = useState(member.role);
  useEffect(() => setRole(member.role), [member.role]);
  return (
    <View style={styles.itemCard}>
      <Text style={styles.itemTitle}>{member.full_name || member.email}</Text>
      <Text style={styles.itemDetail}>
        {member.email} · {member.status}
        {member.is_institution_owner ? " · institution owner" : ""}
      </Text>
      <Field
        label="Role"
        value={role}
        onChangeText={setRole}
        autoCapitalize="none"
      />
      <SmallButton
        title="Save role / transfer ownership"
        disabled={disabled}
        onPress={() => onSave(role)}
      />
      <SmallButton
        title={member.status === "active" ? "Suspend membership" : "Reactivate membership"}
        disabled={disabled || member.is_institution_owner}
        onPress={onToggleStatus}
      />
      {member.is_institution_owner ? (
        <Text style={styles.itemDetail}>
          Transfer ownership before suspending this account.
        </Text>
      ) : null}
    </View>
  );
}

function AdminHome({ institutions, selectedId, onChoose }) {
  return (
    <View>
      <Text style={styles.introText}>
        Choose an institution to open its dashboard and management tools.
      </Text>
      {institutions.length ? (
        institutions.map((item) => (
          <TouchableOpacity
            key={item.id}
            accessibilityRole="button"
            onPress={() => onChoose(item)}
            style={[
              styles.itemCard,
              item.id === selectedId && styles.itemCardSelected,
            ]}
          >
            <Text style={styles.itemTitle}>{item.name}</Text>
            <Text style={styles.itemDetail}>
              {item.role || "Institution administrator"}
            </Text>
            <Text style={styles.actionLink}>Open dashboard  →</Text>
          </TouchableOpacity>
        ))
      ) : (
        <EmptyState
          title="No institution admin access"
          body="Your account does not currently have administrator access to an institution."
        />
      )}
    </View>
  );
}

function AdminOverview({ data, onChoose }) {
  const counts = data?.counts || {};
  return (
    <View>
      <View style={styles.statGrid}>
        {Object.entries(counts).map(([key, value]) => (
          <StatCard
            key={key}
            label={key.replace(/_/g, " ")}
            value={value}
          />
        ))}
      </View>
      <SectionHeading title="Admin tools" />
      <Text style={styles.sectionDescription}>
        Select a section to view and manage its records.
      </Text>
      <View style={styles.shortcutGrid}>
        {adminTabs
          .filter(([, key]) => key !== "overview")
          .map(([label, key]) => (
            <TouchableOpacity
              key={key}
              accessibilityRole="button"
              onPress={() => onChoose(key)}
              style={styles.shortcutCard}
            >
              <Text style={styles.shortcutTitle}>{label}</Text>
              <Text style={styles.shortcutBody}>Manage {label.toLowerCase()}</Text>
            </TouchableOpacity>
          ))}
      </View>
    </View>
  );
}

function ItemList({
  screen,
  items,
  emptyTitle = "Nothing here yet",
  emptyBody = "New items will appear here when they are available.",
  renderAction,
  renderExtra,
  renderAdminItem,
}) {
  if (!items.length) {
    return <EmptyState title={emptyTitle} body={emptyBody} />;
  }
  return (
    <View>
      {items.map((item, index) => {
        if (renderAdminItem) {
          return (
            <View key={item.id ?? index} style={styles.itemCard}>
              {renderAdminItem(item)}
            </View>
          );
        }
        return (
          <View key={item.id ?? index} style={styles.itemCard}>
            <Text style={styles.itemTitle}>{itemTitle(item)}</Text>
            {itemDetails(screen, item) ? (
              <Text style={styles.itemDetail}>{itemDetails(screen, item)}</Text>
            ) : null}
            {item.description ? (
              <Text style={styles.itemBody}>{item.description}</Text>
            ) : null}
            {item.details ? (
              <Text style={styles.itemBody}>{item.details}</Text>
            ) : null}
            {item.response ? (
              <Text style={styles.itemBody}>Response: {item.response}</Text>
            ) : null}
            {item.body && item.title ? (
              <Text style={styles.itemBody}>{item.body}</Text>
            ) : null}
            {item.due_at ? (
              <Text style={styles.itemDetail}>
                Due {formatDate(item.due_at)}
              </Text>
            ) : null}
            {item.date ? (
              <Text style={styles.itemDetail}>{formatDate(item.date)}</Text>
            ) : null}
            {item.poll ? (
              <Text style={styles.itemBody}>
                {item.poll.question} · {item.poll.options?.length || 0} options
              </Text>
            ) : null}
            {item.comments?.length ? (
              <Text style={styles.itemDetail}>
                {item.comments.length} comments
              </Text>
            ) : null}
            {renderAction ? renderAction(item) : null}
            {renderExtra ? renderExtra(item) : null}
          </View>
        );
      })}
    </View>
  );
}

function GroupList({ items, onOpen }) {
  return (
    <View>
      <Text style={styles.introText}>
        Join a group to view its posts and take part in the conversation.
      </Text>
      {items.length ? (
        items.map((group) => (
          <TouchableOpacity
            key={group.id}
            accessibilityRole="button"
            onPress={() => onOpen(group)}
            style={styles.itemCard}
          >
            <Text style={styles.itemTitle}>{group.name}</Text>
            <Text style={styles.itemDetail}>
              {group.type || "Community"} · Tap to join and open
            </Text>
          </TouchableOpacity>
        ))
      ) : (
        <EmptyState
          title="No groups available"
          body="Your institution groups will appear here."
        />
      )}
    </View>
  );
}

function CommunityScreen({
  group,
  items,
  form,
  setField,
  actionBusy,
  onBack,
  onPost,
  onReact,
}) {
  return (
    <View>
      <SecondaryButton title="← All groups" onPress={onBack} />
      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Share with {group?.name}</Text>
        <Field
          label="Write a post"
          value={form.post || ""}
          onChangeText={(value) => setField("post", value)}
          multiline
          placeholder="Share an update with this group"
        />
        <PrimaryButton
          title="Publish post"
          disabled={actionBusy}
          loading={actionBusy}
          onPress={onPost}
        />
      </View>
      {items.length ? (
        items.map((post) => (
          <View key={post.id} style={styles.itemCard}>
            <Text style={styles.itemBody}>{post.body}</Text>
            <Text style={styles.itemDetail}>
              {post.reaction_count || 0} likes
              {post.comments?.length ? ` · ${post.comments.length} comments` : ""}
            </Text>
            <SmallButton
              title="Like"
              disabled={actionBusy}
              onPress={() => onReact(post.id)}
            />
          </View>
        ))
      ) : (
        <EmptyState
          title="Start the conversation"
          body="This group does not have any posts yet."
        />
      )}
    </View>
  );
}

function CommunicationCenter({ token, institution }) {
  const [conversations, setConversations] = useState([]);
  const [selected, setSelected] = useState(null);
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [people, setPeople] = useState([]);
  const [body, setBody] = useState("");
  const [attachmentUrl, setAttachmentUrl] = useState("");
  const [supportTitle, setSupportTitle] = useState("");
  const [supportBody, setSupportBody] = useState("");
  const [groupTitle, setGroupTitle] = useState("");
  const [participantIds, setParticipantIds] = useState([]);
  const [showArchived, setShowArchived] = useState(false);
  const [catalog, setCatalog] = useState({ courses: [], departments: [] });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    setError("");
    setLoading(true);
    try {
      const result = await request(
        `/communications/conversations${showArchived ? "?archived=true" : ""}`,
        token,
      );
      setConversations(result.items || []);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [token, showArchived]);

  useEffect(() => {
    if (!institution?.id) {
      setCatalog({ courses: [], departments: [] });
      return undefined;
    }
    let active = true;
    request(
      `/communications/catalog?institution_id=${institution.id}`,
      token,
    )
      .then((result) => {
        if (active) setCatalog(result);
      })
      .catch((loadError) => {
        if (active) setError(loadError.message);
      });
    return () => {
      active = false;
    };
  }, [token, institution?.id]);

  async function openConversation(conversation) {
    setError("");
    try {
      const [result, conversationResult] = await Promise.all([
        request(`/communications/conversations/${conversation.id}/messages`, token),
        request(
          `/communications/conversations${showArchived ? "?archived=true" : ""}`,
          token,
        ),
      ]);
      setSelected(
        conversationResult.items?.find((item) => item.id === conversation.id) ||
          conversation,
      );
      setMessages(result.items || []);
      await request(
        `/communications/conversations/${conversation.id}/read`,
        token,
        jsonOptions("POST", {}),
      );
      await refresh();
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  async function findPeople() {
    if (query.trim().length < 2) {
      setError("Enter at least two characters to search.");
      return;
    }
    setError("");
    try {
      const result = await request(
        `/search?q=${encodeURIComponent(query.trim())}`,
        token,
      );
      setPeople((result.items || []).filter((item) => item.type === "user"));
    } catch (searchError) {
      setError(searchError.message);
    }
  }

  async function startDirect(person) {
    if (!institution?.id) {
      setError("Join a university before starting a direct conversation.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await request(
        "/communications/conversations",
        token,
        jsonOptions("POST", {
          kind: "direct",
          institution_id: institution.id,
          recipient_id: person.id,
        }),
      );
      const conversation = result.data;
      await refresh();
      await openConversation(conversation);
      setPeople([]);
      setQuery("");
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setBusy(false);
    }
  }

  function blockPerson(person) {
    if (!institution?.id) {
      setError("Join a university before managing communication blocks.");
      return;
    }
    Alert.alert(
      "Block this member?",
      "They will not be able to start or continue direct messages with you.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Block",
          style: "destructive",
          onPress: async () => {
            setError("");
            try {
              await request(
                "/communications/blocks",
                token,
                jsonOptions("POST", {
                  institution_id: institution.id,
                  user_id: person.id,
                }),
              );
              setPeople((current) => current.filter((item) => item.id !== person.id));
            } catch (blockError) {
              setError(blockError.message);
            }
          },
        },
      ],
    );
  }

  async function createSupportRequest() {
    if (!institution?.id || !supportBody.trim()) {
      setError("Choose a university and describe your support request.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await request(
        "/communications/conversations",
        token,
        jsonOptions("POST", {
          kind: "support",
          institution_id: institution.id,
          title: supportTitle.trim() || "Student support request",
          body: supportBody.trim(),
        }),
      );
      setSupportTitle("");
      setSupportBody("");
      await refresh();
      await openConversation(result.data);
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setBusy(false);
    }
  }

  async function createChannel(kind, entityId) {
    if (!institution?.id) {
      setError("Join a university before creating a campus channel.");
      return;
    }
    const payload = {
      kind,
      institution_id: institution.id,
      title: groupTitle.trim(),
    };
    if (kind === "group") {
      payload.participant_ids = participantIds;
      if (!payload.title || !participantIds.length) {
        setError("Enter a group name and add at least one member from search.");
        return;
      }
    }
    if (kind === "course") {
      payload.course_offering_id = Number(entityId);
      payload.official_only = true;
      if (!payload.course_offering_id) {
        setError("Choose a course offering.");
        return;
      }
    }
    if (kind === "department") payload.department_id = Number(entityId);
    setBusy(true);
    setError("");
    try {
      const result = await request(
        "/communications/conversations",
        token,
        jsonOptions("POST", payload),
      );
      setParticipantIds([]);
      await refresh();
      await openConversation(result.data);
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage() {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      await request(
        `/communications/conversations/${selected.id}/messages`,
        token,
        jsonOptions("POST", {
          body: body.trim(),
          attachment_url: attachmentUrl.trim(),
        }),
      );
      setBody("");
      setAttachmentUrl("");
      await openConversation(selected);
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setBusy(false);
    }
  }

  async function changeSetting(changes) {
    if (!selected) return;
    setError("");
    try {
      const result = await request(
        `/communications/conversations/${selected.id}/settings`,
        token,
        jsonOptions("PATCH", changes),
      );
      setSelected((current) => ({
        ...current,
        membership: { ...current.membership, ...result.data },
      }));
      await refresh();
    } catch (actionError) {
      setError(actionError.message);
    }
  }

  async function react(messageId) {
    setError("");
    try {
      await request(
        `/communications/messages/${messageId}/reactions`,
        token,
        jsonOptions("POST", { reaction: "like" }),
      );
      await openConversation(selected);
    } catch (actionError) {
      setError(actionError.message);
    }
  }

  async function report(messageId) {
    setError("");
    try {
      await request(
        `/communications/messages/${messageId}/reports`,
        token,
        jsonOptions("POST", {
          reason: "inappropriate_content",
          details: "Reported from the CampusHub mobile app.",
        }),
      );
      Alert.alert("Report submitted", "Your university moderators can review it.");
    } catch (actionError) {
      setError(actionError.message);
    }
  }

  return (
    <View>
      {error ? <ErrorBanner message={error} /> : null}
      {selected ? (
        <View style={styles.panel}>
          <SecondaryButton
            title="← All conversations"
            onPress={() => {
              setSelected(null);
              refresh();
            }}
          />
          <Text style={styles.panelTitle}>
            {selected.title || selected.participant_names?.join(", ") || "Conversation"}
          </Text>
          <Text style={styles.panelBody}>
            {selected.kind}{selected.official_only ? " · official posts only" : ""}
          </Text>
          <View style={styles.inlineActions}>
            <SmallButton
              title={selected.membership?.muted ? "Unmute" : "Mute"}
              onPress={() => changeSetting({ muted: !selected.membership?.muted })}
            />
            <SmallButton
              title={selected.membership?.pinned ? "Unpin" : "Pin"}
              onPress={() => changeSetting({ pinned: !selected.membership?.pinned })}
            />
            <SmallButton
              title={selected.membership?.archived ? "Unarchive" : "Archive"}
              onPress={() => changeSetting({ archived: !selected.membership?.archived })}
            />
          </View>
          {messages.map((message) => (
            <View key={message.id} style={styles.messageBubble}>
              <Text style={styles.messageAuthor}>
                {message.author_name}{message.official ? " · Official" : ""}
              </Text>
              {message.parent_id ? (
                <Text style={styles.itemDetail}>Reply to message #{message.parent_id}</Text>
              ) : null}
              {message.body ? <Text style={styles.itemBody}>{message.body}</Text> : null}
              {message.attachment_url ? (
                <TouchableOpacity onPress={() => Linking.openURL(message.attachment_url)}>
                  <Text style={styles.link}>{message.attachment_name || "Open attachment"}</Text>
                </TouchableOpacity>
              ) : null}
              <Text style={styles.itemDetail}>{formatDate(message.created_at)}</Text>
              <View style={styles.inlineActions}>
                <SmallButton
                  title={`Like ${message.reactions?.find((item) => item.reaction === "like")?.count || ""}`}
                  onPress={() => react(message.id)}
                />
                <SmallButton title="Report" onPress={() => report(message.id)} />
              </View>
            </View>
          ))}
          {!messages.length ? (
            <EmptyState title="No messages yet" body="Start the conversation below." />
          ) : null}
          <Field
            label="Message"
            value={body}
            onChangeText={setBody}
            multiline
            placeholder="Write a message"
          />
          {!selected.official_only ? (
            <Field
              label="Attachment link"
              value={attachmentUrl}
              onChangeText={setAttachmentUrl}
              autoCapitalize="none"
              keyboardType="url"
              placeholder="https://..."
            />
          ) : null}
          {!selected.official_only ? (
            <PrimaryButton
              title="Send message"
              loading={busy}
              disabled={busy}
              onPress={sendMessage}
            />
          ) : null}
        </View>
      ) : (
        <>
          <View style={styles.panel}>
            <Text style={styles.panelTitle}>Communication Center</Text>
            <Text style={styles.panelBody}>
              Private chat, course discussions, official university updates, and support.
            </Text>
            <SecondaryButton title="Refresh conversations" onPress={refresh} />
            <SecondaryButton
              title={showArchived ? "Hide archived conversations" : "Show archived conversations"}
              onPress={() => setShowArchived((value) => !value)}
            />
          </View>
          <View style={styles.panel}>
            <SectionHeading title="Find a campus member" />
            <Field
              label="Name or username"
              value={query}
              onChangeText={setQuery}
              autoCapitalize="none"
            />
            <PrimaryButton title="Search people" onPress={findPeople} />
            {people.map((person) => (
              <View key={person.id} style={styles.itemCard}>
                <Text style={styles.itemTitle}>{person.title}</Text>
                <View style={styles.inlineActions}>
                  <SmallButton
                    title="Private chat"
                    onPress={() => startDirect(person)}
                  />
                  <SmallButton
                    title={participantIds.includes(person.id) ? "Added" : "Add to group"}
                    disabled={participantIds.includes(person.id)}
                    onPress={() =>
                      setParticipantIds((previous) => [...previous, person.id])
                    }
                  />
                  <SmallButton
                    title="Block"
                    danger
                    onPress={() => blockPerson(person)}
                  />
                </View>
              </View>
            ))}
          </View>
          <View style={styles.panel}>
            <SectionHeading title="Create a group or course channel" />
            <Field
              label="Group name"
              value={groupTitle}
              onChangeText={setGroupTitle}
              placeholder="Project team or class group"
            />
            <Text style={styles.itemDetail}>
              {participantIds.length} members selected from people search
            </Text>
            <PrimaryButton
              title="Create group chat"
              loading={busy}
              disabled={busy}
              onPress={() => createChannel("group")}
            />
            <SectionHeading title="Course discussions and announcements" />
            {catalog.courses.map((course) => (
              <View key={course.id} style={styles.itemCard}>
                <Text style={styles.itemTitle}>
                  {course.course_code} · {course.course_title} · Section {course.section}
                </Text>
                <SecondaryButton
                  title="Open official course channel"
                  onPress={() => createChannel("course", course.id)}
                />
              </View>
            ))}
            {!catalog.courses.length ? (
              <Text style={styles.itemDetail}>No open course offerings found.</Text>
            ) : null}
            {["institution_owner", "institution_admin", "principal"].includes(institution?.role) ? (
              <>
                <SectionHeading title="Department channels" />
                {catalog.departments.map((department) => (
                  <View key={department.id} style={styles.itemCard}>
                    <Text style={styles.itemTitle}>{department.name}</Text>
                    <SecondaryButton
                      title="Create department channel"
                      onPress={() => createChannel("department", department.id)}
                    />
                  </View>
                ))}
                <PrimaryButton
                  title="Create university announcements channel"
                  disabled={busy}
                  onPress={() => createChannel("institution")}
                />
              </>
            ) : null}
          </View>
          <View style={styles.panel}>
            <SectionHeading title="Contact university support" />
            <Field label="Subject" value={supportTitle} onChangeText={setSupportTitle} />
            <Field
              label="How can we help?"
              value={supportBody}
              onChangeText={setSupportBody}
              multiline
            />
            <PrimaryButton
              title="Submit support request"
              loading={busy}
              disabled={busy}
              onPress={createSupportRequest}
            />
          </View>
          {loading ? <ActivityIndicator color="#2563eb" /> : null}
          {conversations.map((conversation) => (
            <TouchableOpacity
              key={conversation.id}
              accessibilityRole="button"
              onPress={() => openConversation(conversation)}
              style={styles.itemCard}
            >
              <Text style={styles.itemTitle}>
                {conversation.title ||
                  conversation.participant_names?.join(", ") ||
                  "Direct conversation"}
              </Text>
              <Text style={styles.itemDetail}>
                {conversation.kind}{conversation.official_only ? " · official" : ""}
                {conversation.unread_count ? ` · ${conversation.unread_count} unread` : ""}
              </Text>
              <Text numberOfLines={2} style={styles.itemBody}>
                {conversation.last_message?.body ||
                  conversation.last_message?.attachment_name ||
                  "No messages yet"}
              </Text>
            </TouchableOpacity>
          ))}
          {!loading && !conversations.length ? (
            <EmptyState
              title="No conversations yet"
              body="Search for a campus member, or send a request to university support."
            />
          ) : null}
        </>
      )}
    </View>
  );
}

function MessagesScreen({
  items,
  user,
  currentUserId,
  form,
  setField,
  actionBusy,
  onOpenChat,
  onBack,
  onSend,
}) {
  if (user) {
    return (
      <View>
        <SecondaryButton title="← All messages" onPress={onBack} />
        <View style={styles.panel}>
          <Text style={styles.panelTitle}>
            Chat with {user.profile?.full_name || "member"}
          </Text>
          {items.map((message) => (
            <View
              key={message.id}
              style={[
                styles.messageBubble,
                message.sender_id === user.user_id && styles.messageBubbleOther,
              ]}
            >
              <Text style={styles.messageAuthor}>
                {message.sender_id === user.user_id
                  ? user.profile?.full_name || "Member"
                  : "You"}
              </Text>
              <Text style={styles.itemBody}>{message.body}</Text>
              {message.created_at ? (
                <Text style={styles.itemDetail}>
                  {formatDate(message.created_at)}
                </Text>
              ) : null}
            </View>
          ))}
          <Field
            label="Message"
            value={form.message || ""}
            onChangeText={(value) => setField("message", value)}
            multiline
            placeholder="Write a message"
          />
          <PrimaryButton
            title="Send message"
            disabled={actionBusy}
            loading={actionBusy}
            onPress={onSend}
          />
        </View>
      </View>
    );
  }

  const conversations = new Map();
  items.forEach((message) => {
    const peerId =
      message.sender_id === currentUserId
        ? message.recipient_id
        : message.sender_id;
    const existing = conversations.get(peerId);
    if (
      !existing ||
      new Date(message.created_at) > new Date(existing.created_at)
    ) {
      conversations.set(peerId, message);
    }
  });
  const threads = [...conversations.entries()].sort(
    ([, first], [, second]) =>
      new Date(second.created_at) - new Date(first.created_at),
  );

  return threads.length ? (
    <View>
      {threads.map(([peerId, latest]) => (
        <TouchableOpacity
          key={peerId}
          accessibilityRole="button"
          onPress={() => onOpenChat(peerId)}
          style={styles.itemCard}
        >
          <Text style={styles.itemTitle}>Conversation with member #{peerId}</Text>
          <Text numberOfLines={2} style={styles.itemBody}>
            {latest.body}
          </Text>
          <Text style={styles.itemDetail}>
            {formatDate(latest.created_at)}  ·  Open conversation →
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  ) : (
    <EmptyState
      title="No conversations yet"
      body="Find a university member and tap Message to start a conversation."
    />
  );
}

function ProfileScreen({
  profile,
  setProfile,
  actionBusy,
  onSave,
  onChangePassword,
  onLogout,
}) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const fields = [
    ["Full name", "full_name"],
    ["Phone", "phone"],
    ["Address", "address"],
    ["Department", "department"],
    ["Program", "program"],
    ["Student ID", "student_id"],
    ["Institution", "institution_text"],
    ["Bio", "bio"],
  ];
  return (
    <View style={styles.panel}>
      <Text style={styles.panelTitle}>Your profile</Text>
      <Text style={styles.panelBody}>
        Keep your details up to date so your university can identify you.
      </Text>
      {fields.map(([label, key]) => (
        <Field
          key={key}
          label={label}
          value={profile[key] || ""}
          onChangeText={(value) =>
            setProfile((current) => ({ ...current, [key]: value }))
          }
          multiline={key === "bio" || key === "address"}
        />
      ))}
      <PrimaryButton
        title="Save profile"
        disabled={actionBusy}
        loading={actionBusy}
        onPress={onSave}
      />
      <SectionHeading title="Change password" />
      <Field
        label="Current password"
        value={currentPassword}
        onChangeText={setCurrentPassword}
        secureTextEntry
        autoCapitalize="none"
      />
      <Field
        label="New password (8+ characters)"
        value={newPassword}
        onChangeText={setNewPassword}
        secureTextEntry
        autoCapitalize="none"
      />
      <SmallButton
        title="Update password"
        disabled={actionBusy || !currentPassword || !newPassword}
        onPress={async () => {
          const changed = await onChangePassword(currentPassword, newPassword);
          if (changed) {
            setCurrentPassword("");
            setNewPassword("");
          }
        }}
      />
      <SecondaryButton title="Sign out" onPress={onLogout} />
    </View>
  );
}

function MemberProfileScreen({ user, onMessage }) {
  const profile = user?.profile || {};
  return (
    <View style={styles.panel}>
      <Text style={styles.panelTitle}>{profile.full_name || "Member profile"}</Text>
      {profile.username ? (
        <Text style={styles.itemDetail}>@{profile.username}</Text>
      ) : null}
      {[
        ["Department", profile.department],
        ["Program", profile.program],
        ["Student ID", profile.student_id],
        ["About", profile.bio],
      ].map(([label, value]) =>
        value ? (
          <Text key={label} style={styles.profileLine}>
            <Text style={styles.profileLabel}>{label}: </Text>
            {value}
          </Text>
        ) : null,
      )}
      <PrimaryButton title="Send message" onPress={onMessage} />
    </View>
  );
}

function RequestForm({
  title,
  fields,
  form,
  setField,
  actionBusy,
  submitTitle,
  onSubmit,
}) {
  return (
    <View style={styles.panel}>
      <Text style={styles.panelTitle}>{title}</Text>
      {fields.map(([label, key]) => (
        <Field
          key={key}
          label={label}
          value={form[key] || ""}
          onChangeText={(value) => setField(key, value)}
          multiline={[
            "details",
            "description",
            "contact",
          ].includes(key)}
          autoCapitalize={key === "item_type" ? "none" : "sentences"}
        />
      ))}
      <PrimaryButton
        title={submitTitle}
        disabled={actionBusy}
        loading={actionBusy}
        onPress={onSubmit}
      />
    </View>
  );
}

function AdminRow({ item, screen, institutionId, onMutate }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(
    item.name || item.title || item.full_name || "",
  );
  const [code, setCode] = useState(item.code || "");
  const [role, setRole] = useState(item.role || "");
  const [status, setStatus] = useState(item.status || "");
  const editMap = {
    members: "members",
    departments: "departments",
    groups: "groups",
    faculties: "faculties",
    programs: "programs",
    adminCourses: "courses",
    adminEvents: "events",
    adminClubs: "clubs",
    adminServices: "service-requests",
    adminFees: "fees",
  };
  const canEdit = Boolean(editMap[screen]);
  const itemId = item.id || item.membership_id;

  if (editing) {
    const update = () => {
      const payload = {
        members: { role, status },
        departments: { name, code },
        groups: { name },
        faculties: { name, code },
        programs: { name, code },
        adminCourses: { title: name, code },
        adminEvents: { title: name },
        adminClubs: { name },
        adminServices: { status },
        adminFees: { title: name },
      }[screen];
      onMutate(
        `/institutions/${institutionId}/admin/${editMap[screen]}/${itemId}`,
        "PUT",
        payload,
        "The record has been updated.",
      );
      setEditing(false);
    };
    return (
      <View>
        {!["members", "adminServices"].includes(screen) ? (
          <Field label="Name" value={name} onChangeText={setName} />
        ) : null}
        {["departments", "faculties", "programs", "adminCourses"].includes(
          screen,
        ) ? (
          <Field label="Code" value={code} onChangeText={setCode} />
        ) : null}
        {screen === "members" ? (
          <>
            <Field label="Role" value={role} onChangeText={setRole} />
            <Field label="Membership status" value={status} onChangeText={setStatus} />
          </>
        ) : null}
        {screen === "adminServices" ? (
          <Field label="Status" value={status} onChangeText={setStatus} />
        ) : null}
        <View style={styles.buttonRow}>
          <SmallButton title="Save" onPress={update} />
          <SmallButton title="Cancel" onPress={() => setEditing(false)} />
        </View>
      </View>
    );
  }

  return (
    <View>
      <Text style={styles.itemTitle}>{itemTitle(item)}</Text>
      {item.email ? <Text style={styles.itemDetail}>{item.email}</Text> : null}
      {itemDetails(screen, item) ? (
        <Text style={styles.itemDetail}>{itemDetails(screen, item)}</Text>
      ) : null}
      {item.details ? <Text style={styles.itemBody}>{item.details}</Text> : null}
      {item.note ? <Text style={styles.itemBody}>{item.note}</Text> : null}
      {canEdit ? (
        <SmallButton title="Edit" onPress={() => setEditing(true)} />
      ) : null}
      {screen === "requests" && item.status === "pending" ? (
        <View style={styles.buttonRow}>
          <SmallButton
            title="Approve"
            onPress={() =>
              onMutate(
                `/institutions/${institutionId}/admin/requests/${item.id}/review`,
                "POST",
                { decision: "approve" },
                "The request has been approved.",
              )
            }
          />
          <SmallButton
            title="Reject"
            danger
            onPress={() =>
              onMutate(
                `/institutions/${institutionId}/admin/requests/${item.id}/review`,
                "POST",
                { decision: "reject" },
                "The request has been rejected.",
              )
            }
          />
        </View>
      ) : null}
    </View>
  );
}

function Field({ label, multiline, style, ...props }) {
  return (
    <View style={styles.fieldGroup}>
      {label ? <Text style={styles.fieldLabel}>{label}</Text> : null}
      <TextInput
        {...props}
        multiline={multiline}
        placeholderTextColor="#94a3b8"
        style={[
          styles.input,
          multiline && styles.multilineInput,
          style,
        ]}
      />
    </View>
  );
}

function PrimaryButton({ title, onPress, disabled, loading }) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      disabled={disabled || loading}
      onPress={onPress}
      style={[
        styles.primaryButton,
        (disabled || loading) && styles.buttonDisabled,
      ]}
    >
      {loading ? (
        <ActivityIndicator color="#fff" />
      ) : (
        <Text style={styles.primaryButtonText}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

function SecondaryButton({ title, onPress }) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      onPress={onPress}
      style={styles.secondaryButton}
    >
      <Text style={styles.secondaryButtonText}>{title}</Text>
    </TouchableOpacity>
  );
}

function SmallButton({ title, onPress, disabled, danger }) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={[
        styles.smallButton,
        danger && styles.dangerButton,
        disabled && styles.buttonDisabled,
      ]}
    >
      <Text style={styles.smallButtonText}>{title}</Text>
    </TouchableOpacity>
  );
}

function IconButton({ label, onPress, accessibilityLabel }) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      style={styles.iconButton}
    >
      <Text style={styles.iconButtonText}>{label}</Text>
    </TouchableOpacity>
  );
}

function StatCard({ label, value }) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function SectionHeading({ title }) {
  return <Text style={styles.sectionHeading}>{title}</Text>;
}

function StatusPill({ label, tone }) {
  return (
    <View style={[styles.statusPill, tone === "success" && styles.successPill]}>
      <Text
        style={[
          styles.statusText,
          tone === "success" && styles.successText,
        ]}
      >
        {label}
      </Text>
    </View>
  );
}

function EmptyState({ title, body, compact }) {
  return (
    <View style={[styles.emptyState, compact && styles.emptyStateCompact]}>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyBody}>{body}</Text>
    </View>
  );
}

function ErrorBanner({ message }) {
  return (
    <View accessibilityRole="alert" style={styles.errorBanner}>
      <Text style={styles.errorText}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f4f7fb" },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
  },
  authScreen: { flex: 1, justifyContent: "center" },
  authScroll: { flexGrow: 1, justifyContent: "center", padding: 20 },
  authCard: {
    backgroundColor: "#fff",
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: "#e8edf5",
    shadowColor: "#1e293b",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.07,
    shadowRadius: 20,
    elevation: 3,
  },
  brandMark: {
    width: 46,
    height: 46,
    borderRadius: 15,
    backgroundColor: "#2563eb",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  brandMarkText: { color: "#fff", fontSize: 24, fontWeight: "800" },
  logo: { fontSize: 30, fontWeight: "800", color: "#0f172a" },
  authSubtitle: { color: "#64748b", marginTop: 6, marginBottom: 18 },
  authLinkButton: { paddingVertical: 14 },
  link: { color: "#2563eb", textAlign: "center", fontWeight: "700" },
  appHeader: {
    minHeight: 76,
    paddingHorizontal: 18,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e8edf5",
  },
  headerTitleGroup: { flex: 1, paddingRight: 10 },
  eyebrow: {
    fontSize: 10,
    letterSpacing: 1.3,
    fontWeight: "800",
    color: "#64748b",
    marginBottom: 3,
  },
  pageTitle: { color: "#0f172a", fontSize: 22, fontWeight: "800" },
  headerSubtitle: { color: "#64748b", fontSize: 12, marginTop: 2 },
  headerActions: { flexDirection: "row", gap: 6 },
  iconButton: {
    minWidth: 40,
    height: 40,
    paddingHorizontal: 8,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f1f5f9",
  },
  iconButtonText: { color: "#334155", fontSize: 19, fontWeight: "700" },
  contentHost: { flex: 1 },
  contentScroll: { flex: 1 },
  content: { padding: 16, paddingBottom: 28, flexGrow: 1 },
  loadingBar: {
    position: "absolute",
    zIndex: 2,
    top: 82,
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#fff",
    elevation: 3,
  },
  loadingText: { color: "#475569", fontSize: 12, fontWeight: "600" },
  welcomePanel: {
    borderRadius: 20,
    padding: 20,
    backgroundColor: "#102b62",
    marginBottom: 14,
  },
  welcomeTitle: {
    color: "#fff",
    fontSize: 23,
    lineHeight: 29,
    fontWeight: "800",
    marginTop: 5,
  },
  welcomeBody: { color: "#cbd9f2", lineHeight: 21, marginTop: 8 },
  statGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: 10,
  },
  statCard: {
    flexGrow: 1,
    flexBasis: "44%",
    backgroundColor: "#fff",
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#e8edf5",
  },
  statValue: { color: "#0f172a", fontSize: 25, fontWeight: "800" },
  statLabel: { color: "#64748b", fontSize: 12, marginTop: 4 },
  sectionHeading: {
    color: "#0f172a",
    fontSize: 18,
    fontWeight: "800",
    marginTop: 16,
    marginBottom: 9,
  },
  sectionDescription: { color: "#64748b", lineHeight: 20, marginBottom: 8 },
  shortcutGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  shortcutCard: {
    flexGrow: 1,
    flexBasis: "44%",
    minHeight: 88,
    padding: 14,
    borderRadius: 16,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#e8edf5",
    justifyContent: "center",
  },
  shortcutTitle: { color: "#172554", fontWeight: "800", fontSize: 14 },
  shortcutBody: { color: "#64748b", fontSize: 12, lineHeight: 17, marginTop: 5 },
  featureSection: { marginBottom: 8 },
  introText: { color: "#64748b", lineHeight: 21, marginBottom: 8 },
  successNotice: {
    color: "#166534",
    backgroundColor: "#dcfce7",
    borderRadius: 12,
    padding: 12,
    lineHeight: 20,
    marginBottom: 12,
  },
  panel: {
    backgroundColor: "#fff",
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#e8edf5",
  },
  panelTitle: { color: "#0f172a", fontSize: 17, fontWeight: "800" },
  panelBody: { color: "#64748b", lineHeight: 20, marginTop: 7 },
  itemCard: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 15,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#e8edf5",
  },
  itemCardSelected: { borderColor: "#2563eb", borderWidth: 1.5 },
  inlineActions: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 },
  nestedCard: {
    backgroundColor: "#f8fafc",
    borderRadius: 12,
    padding: 12,
    marginTop: 10,
    borderWidth: 1,
    borderColor: "#e8edf5",
  },
  loadingContent: { marginVertical: 24 },
  itemTitle: { color: "#0f172a", fontSize: 15, lineHeight: 21, fontWeight: "800" },
  itemDetail: { color: "#64748b", fontSize: 12, lineHeight: 18, marginTop: 5 },
  itemBody: { color: "#334155", lineHeight: 20, marginTop: 7 },
  actionLink: { color: "#2563eb", fontWeight: "700", marginTop: 10 },
  emptyState: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: "#e8edf5",
    alignItems: "center",
    marginTop: 4,
  },
  emptyStateCompact: { padding: 16 },
  emptyTitle: { color: "#0f172a", fontWeight: "800", textAlign: "center" },
  emptyBody: {
    color: "#64748b",
    lineHeight: 20,
    textAlign: "center",
    marginTop: 6,
  },
  fieldGroup: { marginTop: 12 },
  fieldLabel: { color: "#334155", fontSize: 13, fontWeight: "700" },
  input: {
    minHeight: 46,
    borderWidth: 1,
    borderColor: "#d7dfeb",
    borderRadius: 12,
    paddingHorizontal: 13,
    paddingVertical: 11,
    marginTop: 6,
    color: "#0f172a",
    backgroundColor: "#fff",
  },
  multilineInput: { minHeight: 86, textAlignVertical: "top" },
  primaryButton: {
    minHeight: 46,
    backgroundColor: "#2563eb",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 14,
  },
  primaryButtonText: { color: "#fff", fontWeight: "800", textAlign: "center" },
  secondaryButton: {
    minHeight: 43,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#d7dfeb",
    borderRadius: 12,
    backgroundColor: "#fff",
  },
  secondaryButtonText: { color: "#334155", fontWeight: "700" },
  smallButton: {
    minHeight: 38,
    paddingHorizontal: 13,
    paddingVertical: 9,
    borderRadius: 10,
    marginTop: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#2563eb",
  },
  dangerButton: { backgroundColor: "#b42318" },
  smallButtonText: { color: "#fff", fontWeight: "700", fontSize: 12 },
  buttonRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  buttonDisabled: { opacity: 0.55 },
  statusPill: {
    alignSelf: "flex-start",
    marginTop: 10,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: "#f1f5f9",
  },
  statusText: { color: "#475569", fontSize: 12, fontWeight: "700" },
  successPill: { backgroundColor: "#dcfce7" },
  successText: { color: "#166534" },
  inlineForm: { marginTop: 7 },
  messageBubble: {
    backgroundColor: "#eff6ff",
    padding: 12,
    borderRadius: 14,
    marginTop: 10,
    alignSelf: "flex-end",
    maxWidth: "90%",
  },
  messageBubbleOther: {
    backgroundColor: "#f1f5f9",
    alignSelf: "flex-start",
  },
  messageAuthor: { color: "#475569", fontSize: 11, fontWeight: "800" },
  profileLine: { color: "#334155", lineHeight: 21, marginTop: 10 },
  profileLabel: { color: "#64748b", fontWeight: "700" },
  errorBanner: {
    backgroundColor: "#fff1f0",
    borderBottomWidth: 1,
    borderBottomColor: "#fecaca",
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  errorText: { color: "#b42318", lineHeight: 18 },
  bottomNav: {
    minHeight: 62,
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#e8edf5",
    paddingHorizontal: 5,
    paddingBottom: Platform.OS === "ios" ? 4 : 0,
  },
  navButton: {
    flex: 1,
    minHeight: 52,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 13,
  },
  navButtonActive: { backgroundColor: "#eff6ff" },
  navIcon: { color: "#64748b", fontSize: 18, fontWeight: "700" },
  navLabel: { color: "#64748b", fontSize: 10, fontWeight: "700", marginTop: 2 },
  navTextActive: { color: "#1d4ed8" },
});
