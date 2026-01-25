import { useAuth } from '../context/AuthContext'

export default function UserMenu() {
  const { user } = useAuth()

  if (!user) return null

  return (
    <div className="flex items-center space-x-2">
      {user.picture_url ? (
        <img
          src={user.picture_url}
          alt={user.name || user.email}
          className="w-8 h-8 rounded-full border-2 border-white"
        />
      ) : (
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium border-2 border-white">
          {(user.name || user.email)[0].toUpperCase()}
        </div>
      )}
      <span className="text-white text-sm hidden md:block">
        {user.name || user.email}
      </span>
      <span className="text-blue-200 text-xs hidden md:block">(Demo)</span>
    </div>
  )
}
