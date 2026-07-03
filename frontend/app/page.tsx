import Link from "next/link";

// Server-rendered landing page.
export default function Home() {
  return (
    <div className="center">
      <div className="card auth-box">
        <h1 style={{ color: "var(--green)", textAlign: "center" }}>Mediminder</h1>
        <p style={{ textAlign: "center", color: "#6b7280" }}>
          Your medicine reminder, in the browser.
        </p>
        <Link href="/login">
          <button className="btn" style={{ width: "100%", marginTop: 12 }}>
            User Login
          </button>
        </Link>
        <Link href="/register">
          <button className="btn ghost" style={{ width: "100%", marginTop: 10 }}>
            Register
          </button>
        </Link>
        <Link href="/admin-login">
          <button className="btn teal" style={{ width: "100%", marginTop: 10 }}>
            Admin Login
          </button>
        </Link>
      </div>
    </div>
  );
}
