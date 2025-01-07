'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const departments = ['Engineering', 'Product', 'Design', 'Marketing', 'Sales', 'HR']
const workTypes = ['Remote', 'Hybrid', 'On-site']

export function RoleDialog({ open, onOpenChange, role }) {
  const [formData, setFormData] = useState({
    name: '',
    department: '',
    workType: '',
    salary: '',
    experience: '',
  })

  useEffect(() => {
    if (role) {
      setFormData(role)
    } else {
      setFormData({
        name: '',
        department: '',
        workType: '',
        salary: '',
        experience: '',
      })
    }
  }, [role])

  const handleSubmit = (e) => {
    e.preventDefault()
    // Implement form submission logic here
    console.log('Form submitted:', formData)
    onOpenChange(false)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{role ? 'Edit Role' : 'Create New Role'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Role Name</Label>
            <Input
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="department">Department</Label>
            <Select
              name="department"
              value={formData.department}
              onValueChange={(value) => setFormData((prev) => ({ ...prev, department: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select department" />
              </SelectTrigger>
              <SelectContent>
                {departments.map((dept) => (
                  <SelectItem key={dept} value={dept}>
                    {dept}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="workType">Work Type</Label>
            <Select
              name="workType"
              value={formData.workType}
              onValueChange={(value) => setFormData((prev) => ({ ...prev, workType: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select work type" />
              </SelectTrigger>
              <SelectContent>
                {workTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="salary">Salary Range</Label>
            <Input
              id="salary"
              name="salary"
              value={formData.salary}
              onChange={handleChange}
              placeholder="e.g., $50,000 - $80,000"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="experience">Required Experience</Label>
            <Input
              id="experience"
              name="experience"
              value={formData.experience}
              onChange={handleChange}
              placeholder="e.g., 2-3 years"
            />
          </div>
          <DialogFooter>
            <Button type="submit">Save Role</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

