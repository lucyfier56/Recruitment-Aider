import '@/app/globals.css'
import { Inter } from 'next/font/google'
import { SidebarProvider } from '@/components/ui/sidebar'
import Sidebar from '@/components/Sidebar'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Recruitment Management System',
  description: 'A professional minimalist recruitment management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <SidebarProvider>
          <div className="flex h-screen">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-6">
              {children}
            </main>
          </div>
        </SidebarProvider>
      </body>
    </html>
  )
}

