import { AdminProviders } from './app/providers/AdminProviders'
import { AdminRouter } from './app/router/AdminRouter'

export default function App() {
  return (
    <AdminProviders>
      <AdminRouter />
    </AdminProviders>
  )
}
