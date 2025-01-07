'use client'

import { useState } from 'react'
import RolesTable from '@/components/RolesTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Plus, Search } from 'lucide-react'
import { RoleDialog } from '@/components/RoleDialog'

export default function RolesPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold tracking-tight">Manage Roles</h1>
        <div className="flex space-x-2">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-500 h-4 w-4" />
            <Input
              type="text"
              placeholder="Search roles..."
              className="pl-8 pr-4"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Create Role
          </Button>
        </div>
      </div>
      <RolesTable searchQuery={searchQuery} />
      <RoleDialog open={dialogOpen} onOpenChange={setDialogOpen} role={null} />
    </div>
  )
}

