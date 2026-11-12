import { useAuth } from './AuthContext.jsx'
import Icon from './Icon.jsx'

export default function SignOutButton() {
  const { user, logout } = useAuth()
  return (
    <button
      type="button"
      className="icon-btn"
      aria-label={`Sign out ${user?.display_name ?? ''}`.trim()}
      title="Sign out"
      onClick={() => {
        if (window.confirm('Sign out of ChalkBox?')) logout()
      }}
    >
      <Icon name="logout" />
    </button>
  )
}
